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
_DATA_DIR = os.path.dirname(_DB_PATH) or "."
_LOG_DIR = os.environ.get("EXPERIMENT_LOG_DIR", "/app/logs")


def _ensure_db_dir() -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    os.makedirs(_LOG_DIR, exist_ok=True)


def _connect() -> sqlite3.Connection:
    _ensure_db_dir()
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
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
                session_id  TEXT    NOT NULL UNIQUE,
                timestamp   TEXT    NOT NULL,
                decision    TEXT    NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_decisions_session ON decisions(session_id);
            CREATE INDEX IF NOT EXISTS idx_decisions_ts      ON decisions(timestamp);

            CREATE TABLE IF NOT EXISTS paper_trades (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp    TEXT    NOT NULL,
                action       TEXT    NOT NULL CHECK(action IN ('buy','sell')),
                ticker       TEXT    NOT NULL,
                price        REAL    NOT NULL,
                quantity     REAL    NOT NULL,
                stop_price   REAL,
                target_price REAL,
                reason       TEXT,
                session_id   TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_trades_ticker ON paper_trades(ticker);
            CREATE INDEX IF NOT EXISTS idx_trades_ts     ON paper_trades(timestamp);
        """)
        # Migrate existing DBs: add columns if absent
        for col, typedef in [("stop_price", "REAL"), ("target_price", "REAL")]:
            try:
                conn.execute(f"ALTER TABLE paper_trades ADD COLUMN {col} {typedef}")
            except sqlite3.OperationalError:
                pass  # column already exists


# ---------------------------------------------------------------------------
# Decisions
# ---------------------------------------------------------------------------

def save_decision(session_id: str, decision: dict) -> int:
    init_db()
    ts = datetime.now(timezone.utc).isoformat()
    decision_json = json.dumps(decision, ensure_ascii=False)
    with _db() as conn:
        # Idempotent: return existing row if session_id already saved
        existing = conn.execute(
            "SELECT id FROM decisions WHERE session_id = ?", (session_id,)
        ).fetchone()
        if existing:
            return existing["id"]
        cur = conn.execute(
            "INSERT INTO decisions (session_id, timestamp, decision) VALUES (?, ?, ?)",
            (session_id, ts, decision_json),
        )
        row_id = cur.lastrowid

    log_date = ts[:10]  # YYYY-MM-DD
    log_path = os.path.join(_LOG_DIR, f"{log_date}.log")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{ts} | {session_id} | {decision_json}\n")

    return row_id


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
    stop_price: Optional[float] = None,
    target_price: Optional[float] = None,
) -> int:
    init_db()
    if action.lower() == "buy" and stop_price is not None and stop_price >= price:
        raise ValueError(f"stop_price {stop_price} >= entry {price} — invalid for buy")
    if action.lower() == "sell" and stop_price is not None and stop_price <= price:
        raise ValueError(f"stop_price {stop_price} <= entry {price} — invalid for sell")
    ts = datetime.now(timezone.utc).isoformat()
    with _db() as conn:
        cur = conn.execute(
            """INSERT INTO paper_trades
               (timestamp, action, ticker, price, quantity, stop_price, target_price, reason, session_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (ts, action.lower(), ticker.upper(), price, quantity, stop_price, target_price, reason, session_id),
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


def get_trade_outcomes(
    since_date: Optional[str] = None,
    initial_capital: float = 5000.0,
) -> dict:
    """
    P&L summary of all trades since since_date (YYYY-MM-DD).
    Returns completed trades, cash balance, open positions, and capital summary.
    """
    init_db()
    with _db() as conn:
        # Period rows for realized P&L reporting
        if since_date:
            rows = conn.execute(
                "SELECT * FROM paper_trades WHERE date(timestamp) >= ? ORDER BY timestamp ASC",
                (since_date,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM paper_trades ORDER BY timestamp ASC"
            ).fetchall()

        # All-time totals for accurate cash balance (unaffected by since_date filter)
        totals = conn.execute(
            """SELECT
                COALESCE(SUM(CASE WHEN action='buy'  THEN price*quantity ELSE 0 END), 0) AS total_buy,
                COALESCE(SUM(CASE WHEN action='sell' THEN price*quantity ELSE 0 END), 0) AS total_sell
               FROM paper_trades"""
        ).fetchone()

    total_buy_value = float(totals["total_buy"])
    total_sell_value = float(totals["total_sell"])
    cash_balance = initial_capital - total_buy_value + total_sell_value

    completed: list[dict] = []
    open_positions = get_paper_portfolio()

    # FIFO realized P&L for the filtered period
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
    cost_of_open = sum(p["total_cost_brl"] for p in open_positions)

    return {
        "completed_trades": completed,
        "realized_pnl_brl": round(realized_pnl, 2),
        "realized_pnl_pct": round(realized_pnl / initial_capital * 100, 2) if initial_capital else 0.0,
        "open_positions": open_positions,
        "open_positions_cost_brl": round(cost_of_open, 2),
        "cash_balance_brl": round(cash_balance, 2),
        "total_invested_brl": round(total_buy_value, 2),
        "total_proceeds_brl": round(total_sell_value, 2),
        "initial_capital_brl": initial_capital,
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
            "ROUND(price*quantity,2) as trade_value_brl, stop_price, target_price, reason, session_id "
            "FROM paper_trades ORDER BY timestamp ASC"
        ).fetchall()
        decisions = conn.execute(
            "SELECT id, session_id, timestamp, decision FROM decisions ORDER BY timestamp ASC"
        ).fetchall()

    # --- trades CSV ---
    trades_buf = io.StringIO()
    tw = csv.writer(trades_buf)
    tw.writerow(["id", "timestamp", "action", "ticker", "price", "quantity",
                 "trade_value_brl", "stop_price", "target_price", "reason", "session_id"])
    for r in trades:
        tw.writerow([r["id"], r["timestamp"], r["action"], r["ticker"],
                     r["price"], r["quantity"], r["trade_value_brl"],
                     r["stop_price"] or "", r["target_price"] or "",
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
