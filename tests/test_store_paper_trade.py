import sqlite3

import pytest

from tests.conftest import count_trades


def _buy(store, **kw):
    args = dict(action="buy", ticker="PETR4", price=30.0, quantity=10, session_id="s1")
    args.update(kw)
    return store.save_paper_trade(**args)


def test_returns_saved_trade_namedtuple(store):
    r = _buy(store)
    assert r.created is True
    assert isinstance(r.id, int)
    assert r.trade["ticker"] == "PETR4"
    assert r.trade["idempotency_key"] == "s1:buy:PETR4"


def test_duplicate_with_session_id_is_one_row(store):
    first = _buy(store)
    second = _buy(store)
    assert second.id == first.id
    assert second.created is False
    assert count_trades(store) == 1


def test_explicit_different_key_creates_second_row(store):
    first = _buy(store, idempotency_key="s1:buy:PETR4:1")
    second = _buy(store, idempotency_key="s1:buy:PETR4:2")
    assert second.created is True
    assert second.id != first.id
    assert count_trades(store) == 2


def test_same_explicit_key_is_duplicate(store):
    _buy(store, idempotency_key="k")
    again = _buy(store, idempotency_key="k", price=99.0)
    assert again.created is False
    assert again.trade["price"] == 30.0  # devolve a linha existente
    assert count_trades(store) == 1


def test_sell_same_ticker_same_session_is_saved(store):
    b = _buy(store)
    s = _buy(store, action="sell", price=33.0)
    assert s.created is True
    assert s.id != b.id
    assert s.trade["idempotency_key"] == "s1:sell:PETR4"
    assert count_trades(store) == 2


def test_no_session_no_key_duplicates(store):
    a = _buy(store, session_id=None)
    b = _buy(store, session_id=None)
    assert a.created and b.created
    assert a.id != b.id
    assert a.trade["idempotency_key"] is None
    assert count_trades(store) == 2


def test_whitespace_key_falls_back_to_derived(store):
    r = _buy(store, idempotency_key="   ")
    assert r.trade["idempotency_key"] == "s1:buy:PETR4"


def test_explicit_key_is_stripped(store):
    r = _buy(store, idempotency_key="  abc  ")
    assert r.trade["idempotency_key"] == "abc"


def test_derived_key_normalizes_case(store):
    assert (
        store.paper_trade_idempotency_key("BUY", "petr4", "s1", None) == "s1:buy:PETR4"
    )
    a = _buy(store, ticker="petr4")
    b = _buy(store, ticker="PETR4")
    assert b.created is False and b.id == a.id


def test_whitespace_session_and_no_key_is_none(store):
    assert store.paper_trade_idempotency_key("buy", "PETR4", "  ", None) is None


def test_invalid_buy_stop_raises(store):
    with pytest.raises(ValueError):
        _buy(store, stop_price=30.0)  # stop >= entry
    with pytest.raises(ValueError):
        _buy(store, stop_price=35.0)
    assert count_trades(store) == 0


def test_invalid_sell_stop_raises(store):
    with pytest.raises(ValueError):
        _buy(store, action="sell", stop_price=29.0)  # stop <= price
    assert count_trades(store) == 0


def test_valid_stop_saved(store):
    r = _buy(store, stop_price=27.6, target_price=36.0)
    assert r.trade["stop_price"] == 27.6
    assert r.trade["target_price"] == 36.0


def test_migration_old_db_without_idempotency_key_preserves_rows(store):
    import os

    os.makedirs(store._DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(store._DB_PATH)
    conn.executescript("""
        CREATE TABLE paper_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            action TEXT NOT NULL CHECK(action IN ('buy','sell')),
            ticker TEXT NOT NULL,
            price REAL NOT NULL,
            quantity REAL NOT NULL,
            reason TEXT,
            session_id TEXT
        );
        INSERT INTO paper_trades (timestamp, action, ticker, price, quantity, reason, session_id)
        VALUES ('2026-05-20T10:00:00+00:00', 'buy', 'VALE3', 60.0, 5, 'legado', 'old'),
               ('2026-05-21T10:00:00+00:00', 'buy', 'VALE3', 60.0, 5, 'legado', 'old');
    """)
    conn.commit()
    conn.close()

    store.init_db()

    with store._db() as c:
        rows = c.execute("SELECT * FROM paper_trades ORDER BY id").fetchall()
        cols = {r["name"] for r in c.execute("PRAGMA table_info(paper_trades)")}
    assert len(rows) == 2
    assert {"idempotency_key", "stop_price", "target_price"} <= cols
    assert all(r["idempotency_key"] is None for r in rows)
    assert rows[0]["reason"] == "legado"

    # Linhas legadas (chave NULL) não conflitam; trade novo funciona.
    r = _buy(store, ticker="VALE3", price=61.0)
    assert r.created is True
    assert count_trades(store) == 3
    # init_db é idempotente
    store.init_db()
    assert count_trades(store) == 3
