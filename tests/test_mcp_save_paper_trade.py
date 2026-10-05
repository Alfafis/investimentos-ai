import pytest

from mcp_server import server


def test_new_trade_response(store):
    r = server.save_paper_trade(
        "buy", "PETR4", 30.0, 10, reason="teste", session_id="s1",
        stop_price=27.6, target_price=36.0,
    )
    assert r["saved"] is True
    assert r["duplicate"] is False
    assert r["trade_value_brl"] == 300.0
    assert r["stop_price"] == 27.6
    assert r["target_price"] == 36.0
    assert r["idempotency_key"] == "s1:buy:PETR4"
    assert "existing_trade" not in r


def test_duplicate_response_has_existing_trade(store):
    first = server.save_paper_trade("buy", "PETR4", 30.0, 10, session_id="s1", reason="r1")
    second = server.save_paper_trade("buy", "PETR4", 31.0, 99, session_id="s1", reason="r2")
    assert second["saved"] is True
    assert second["duplicate"] is True
    assert second["id"] == first["id"]
    ex = second["existing_trade"]
    assert ex["price"] == 30.0 and ex["quantity"] == 10 and ex["reason"] == "r1"
    assert ex["session_id"] == "s1" and ex["action"] == "buy" and ex["ticker"] == "PETR4"
    assert "message" in second


def test_invalid_action_returns_error(store):
    assert "error" in server.save_paper_trade("hold", "PETR4", 30.0, 1)


def test_invalid_stop_returns_error(store):
    r = server.save_paper_trade("buy", "PETR4", 30.0, 1, stop_price=31.0)
    assert "error" in r


def test_tool_count_is_23():
    import asyncio

    tools = asyncio.run(server.mcp.list_tools())
    assert len(tools) == 23
