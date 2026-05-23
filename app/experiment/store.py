"""
SQLite-backed persistence for the 5-day agent experiment.

Tables:
  decisions   — full agent decision context per iteration
  paper_trades — virtual buy/sell actions (paper trading)
"""
import csv
import io
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from typing import Optional

_DB_PATH = os.environ.get("EXPERIMENT_DB_PATH", "/data/experiment.db")


def _ensure_db_dir() -> None:
    db_dir = os.path.dirname(_DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)


def _connect() -> sqlite3.Connection:
    _ensure_db_dir()
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def _db():
    conn = _connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS decisions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  TEXT    NOT NULL,
                timestamp   TEXT    NOT NULL,
                decision    TEXT    NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_decisions_session ON decisions(session_id);
            CREATE INDEX IF NOT EXISTS idx_decisions_ts      ON decisions(timestamp);

            CREATE TABLE IF NOT EXISTS paper_trades (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT    NOT NULL,
                action      TEXT    NOT NULL CHECK(action IN ('buy','sell')),
                ticker      TEXT    NOT NULL,
                price       REAL    NOT NULL,
                quantity    REAL    NOT NULL,
                reason      TEXT,
                session_id  TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_trades_ticker ON paper_trades(ticker);
            CREATE INDEX IF NOT EXISTS idx_trades_ts     ON paper_trades(timestamp);
        """)


# ---------------------------------------------------------------------------
# Decisions
# ---------------------------------------------------------------------------

def save_decision(session_id: str, decision: dict) -> int:
    init_db()
    ts = datetime.now(timezone.utc).isoformat()
    with _db() as conn:
        cur = conn.execute(
            "INSERT INTO decisions (session_id, timestamp, decision) VALUES (?, ?, ?)",
            (session_id, ts, json.dumps(decision, ensure_ascii=False)),
        )
        return cur.lastrowid


def get_decision_log(
    date_filter: Optional[str] = None,
    last_n: Optional[int] = None,
) -> list[dict]:
    init_db()
    with _db() as conn:
        if date_filter:
            rows = conn.execute(
                "SELECT * FROM decisions WHERE date(timestamp) = ? ORDER BY timestamp ASC",
                (date_filter,),
            ).fetchall()
        elif last_n:
            rows = conn.execute(
                "SELECT * FROM decisions ORDER BY timestamp DESC LIMIT ?",
                (last_n,),
            ).fetchall()
            rows = list(reversed(rows))
        else:
            rows = conn.execute(
                "SELECT * FROM decisions ORDER BY timestamp ASC"
            ).fetchall()

    return [
        {
            "id": r["id"],
            "session_id": r["session_id"],
            "timestamp": r["timestamp"],
            "decision": json.loads(r["decision"]),
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Paper trades
# ---------------------------------------------------------------------------

def save_paper_trade(
    action: str,
    ticker: str,
    price: float,
    quantity: float,
    reason: Optional[str] = None,
    session_id: Optional[str] = None,
) -> int:
    init_db()
    ts = datetime.now(timezone.utc).isoformat()
    with _db() as conn:
        cur = conn.execute(
            """INSERT INTO paper_trades
               (timestamp, action, ticker, price, quantity, reason, session_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (ts, action.lower(), ticker.upper(), price, quantity, reason, session_id),
        )
        return cur.lastrowid


def get_paper_portfolio() -> list[dict]:
    """Return open positions: buys not yet fully offset by sells, with avg cost."""
    init_db()
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM paper_trades ORDER BY timestamp ASC"
        ).fetchall()

    # FIFO matching
    buys: dict[str, list[dict]] = {}
    sells: dict[str, list[dict]] = {}
    for r in rows:
        t = r["ticker"]
        entry = {
            "timestamp": r["timestamp"],
            "price": r["price"],
            "quantity": r["quantity"],
            "reason": r["reason"],
            "session_id": r["session_id"],
        }
        if r["action"] == "buy":
            buys.setdefault(t, []).append(entry)
        else:
            sells.setdefault(t, []).append(entry)

    positions = []
    for ticker, buy_list in buys.items():
        total_qty = sum(b["quantity"] for b in buy_list)
        sold_qty = sum(s["quantity"] for s in sells.get(ticker, []))
        open_qty = total_qty - sold_qty
        if open_qty <= 0:
            continue
        # weighted avg price of all buys (simplified — good enough for 5-day experiment)
        total_cost = sum(b["quantity"] * b["price"] for b in buy_list)
        avg_price = total_cost / total_qty
        positions.append({
            "ticker": ticker,
            "open_quantity": round(open_qty, 4),
            "avg_buy_price": round(avg_price, 4),
            "total_cost_brl": round(open_qty * avg_price, 2),
            "first_buy_at": buy_list[0]["timestamp"],
        })

    return positions


def get_trade_outcomes(since_date: Optional[str] = None) -> dict:
    """
    P&L summary of all trades since since_date (YYYY-MM-DD).
    Returns completed trades (buy+sell pairs) and open positions.
    """
    init_db()
    with _db() as conn:
        if since_date:
            rows = conn.execute(
                "SELECT * FROM paper_trades WHERE date(timestamp) >= ? ORDER BY timestamp ASC",
                (since_date,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM paper_trades ORDER BY timestamp ASC"
            ).fetchall()

    completed: list[dict] = []
    open_positions = get_paper_portfolio()

    # Group by ticker for realized P&L (FIFO)
    by_ticker: dict[str, list] = {}
    for r in rows:
        by_ticker.setdefault(r["ticker"], []).append(r)

    for ticker, trades in by_ticker.items():
        buy_queue: list[dict] = []
        for t in trades:
            if t["action"] == "buy":
                buy_queue.append({"price": t["price"], "qty": t["quantity"], "ts": t["timestamp"]})
            else:  # sell
                sell_qty = t["quantity"]
                sell_price = t["price"]
                while sell_qty > 0 and buy_queue:
                    buy = buy_queue[0]
                    matched = min(buy["qty"], sell_qty)
                    pnl = (sell_price - buy["price"]) * matched
                    pnl_pct = (sell_price - buy["price"]) / buy["price"] * 100
                    completed.append({
                        "ticker": ticker,
                        "buy_at": buy["ts"],
                        "sell_at": t["timestamp"],
                        "quantity": matched,
                        "buy_price": buy["price"],
                        "sell_price": sell_price,
                        "pnl_brl": round(pnl, 2),
                        "pnl_pct": round(pnl_pct, 2),
                    })
                    buy["qty"] -= matched
                    sell_qty -= matched
                    if buy["qty"] <= 0:
                        buy_queue.pop(0)

    realized_pnl = sum(c["pnl_brl"] for c in completed)

    return {
        "completed_trades": completed,
        "realized_pnl_brl": round(realized_pnl, 2),
        "open_positions": open_positions,
        "period_from": since_date or "all-time",
    }


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def export_experiment_csv() -> dict:
    """
    Export all experiment data to CSV strings + write files to /data/.

    Returns dict with:
      - trades_csv: paper_trades as CSV string
      - decisions_csv: decisions as CSV string (decision column as JSON)
      - trades_path: file path written on disk
      - decisions_path: file path written on disk
    """
    init_db()
    with _db() as conn:
        trades = conn.execute(
            "SELECT id, timestamp, action, ticker, price, quantity, "
            "ROUND(price*quantity,2) as trade_value_brl, reason, session_id "
            "FROM paper_trades ORDER BY timestamp ASC"
        ).fetchall()
        decisions = conn.execute(
            "SELECT id, session_id, timestamp, decision FROM decisions ORDER BY timestamp ASC"
        ).fetchall()

    # --- trades CSV ---
    trades_buf = io.StringIO()
    tw = csv.writer(trades_buf)
    tw.writerow(["id", "timestamp", "action", "ticker", "price", "quantity",
                 "trade_value_brl", "reason", "session_id"])
    for r in trades:
        tw.writerow([r["id"], r["timestamp"], r["action"], r["ticker"],
                     r["price"], r["quantity"], r["trade_value_brl"],
                     r["reason"] or "", r["session_id"] or ""])
    trades_csv = trades_buf.getvalue()

    # --- decisions CSV ---
    decisions_buf = io.StringIO()
    dw = csv.writer(decisions_buf)
    dw.writerow(["id", "session_id", "timestamp", "decision_json"])
    for r in decisions:
        dw.writerow([r["id"], r["session_id"], r["timestamp"], r["decision"]])
    decisions_csv = decisions_buf.getvalue()

    # Write to /data/ so user can docker cp out
    db_dir = os.path.dirname(_DB_PATH)
    trades_path = os.path.join(db_dir, "trades.csv")
    decisions_path = os.path.join(db_dir, "decisions.csv")
    with open(trades_path, "w", encoding="utf-8", newline="") as f:
        f.write(trades_csv)
    with open(decisions_path, "w", encoding="utf-8", newline="") as f:
        f.write(decisions_csv)

    return {
        "trades_csv": trades_csv,
        "decisions_csv": decisions_csv,
        "trades_path": trades_path,
        "decisions_path": decisions_path,
        "trades_count": len(trades),
        "decisions_count": len(decisions),
    }
