import pytest

from tests.conftest import insert_trade


def _pos(store, ticker):
    return {p["ticker"]: p for p in store.get_paper_portfolio()}.get(ticker)


def test_open_quantity_and_weighted_avg_cost(store):
    insert_trade(store, "2026-05-25T10:00:00", "buy", "PETR4", 30.0, 10)
    insert_trade(store, "2026-05-26T10:00:00", "buy", "PETR4", 36.0, 20)
    p = _pos(store, "PETR4")
    assert p["open_quantity"] == 30
    assert p["avg_buy_price"] == pytest.approx(34.0)  # (300+720)/30
    assert p["total_cost_brl"] == pytest.approx(1020.0)
    assert p["first_buy_at"] == "2026-05-25T10:00:00"


def test_partial_sell_reduces_open_quantity(store):
    insert_trade(store, "2026-05-25T10:00:00", "buy", "VALE3", 60.0, 10)
    insert_trade(store, "2026-05-26T10:00:00", "sell", "VALE3", 66.0, 4)
    p = _pos(store, "VALE3")
    assert p["open_quantity"] == 6
    assert p["avg_buy_price"] == 60.0
    assert p["total_cost_brl"] == pytest.approx(360.0)


def test_fully_sold_position_disappears(store):
    insert_trade(store, "2026-05-25T10:00:00", "buy", "VALE3", 60.0, 10)
    insert_trade(store, "2026-05-26T10:00:00", "sell", "VALE3", 66.0, 10)
    assert _pos(store, "VALE3") is None
    assert store.get_paper_portfolio() == []


def test_tickers_are_independent(store):
    insert_trade(store, "2026-05-25T10:00:00", "buy", "VALE3", 60.0, 10)
    insert_trade(store, "2026-05-25T11:00:00", "buy", "ITUB4", 30.0, 5)
    insert_trade(store, "2026-05-26T10:00:00", "sell", "VALE3", 66.0, 10)
    assert [p["ticker"] for p in store.get_paper_portfolio()] == ["ITUB4"]


def test_outcomes_use_fifo_for_realized_pnl(store):
    insert_trade(store, "2026-05-25T10:00:00", "buy", "PETR4", 30.0, 10)
    insert_trade(store, "2026-05-26T10:00:00", "buy", "PETR4", 40.0, 10)
    insert_trade(store, "2026-05-27T10:00:00", "sell", "PETR4", 50.0, 15)
    out = store.get_trade_outcomes(initial_capital=5000.0)
    legs = out["completed_trades"]
    assert [(l["quantity"], l["buy_price"]) for l in legs] == [(10, 30.0), (5, 40.0)]
    assert out["realized_pnl_brl"] == pytest.approx(10 * 20 + 5 * 10)
    assert out["cash_balance_brl"] == pytest.approx(5000 - 700 + 750)


def test_mcp_get_paper_portfolio(store):
    from mcp_server import server
    insert_trade(store, "2026-05-25T10:00:00", "buy", "VALE3", 60.0, 10)
    r = server.get_paper_portfolio()
    assert r["count"] == 1 and r["positions"][0]["ticker"] == "VALE3"


@pytest.mark.xfail(strict=True, reason=(
    "BUG: get_paper_portfolio documenta FIFO, mas avg_buy_price é a média ponderada de "
    "TODAS as compras, sem baixar os lotes consumidos pelas vendas. Após vender o 1º lote "
    "inteiro, o custo médio restante deveria ser o do 2º lote (40.0), mas sai 35.0."
))
def test_bug_avg_cost_ignores_fifo_consumption(store):
    insert_trade(store, "2026-05-25T10:00:00", "buy", "PETR4", 30.0, 10)
    insert_trade(store, "2026-05-26T10:00:00", "buy", "PETR4", 40.0, 10)
    insert_trade(store, "2026-05-27T10:00:00", "sell", "PETR4", 50.0, 10)
    p = _pos(store, "PETR4")
    assert p["avg_buy_price"] == pytest.approx(40.0)
