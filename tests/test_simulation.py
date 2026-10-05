"""Strategies e engine com séries sintéticas. Sem rede: _fetch_ohlcv é substituído."""
import numpy as np
import pandas as pd
import pytest

from app.simulation import engine
from app.simulation.strategies import (
    STRATEGIES,
    combined_strategy,
    dividend_value_strategy,
    ema_crossover_strategy,
    rsi_strategy,
)

WARMUP = 120


def make_df(closes) -> pd.DataFrame:
    idx = pd.bdate_range("2025-01-02", periods=len(closes))
    return pd.DataFrame({"Close": [float(c) for c in closes]}, index=idx)


def pullback_series(drop=0.985, drop_days=8, rise=1.03, rise_days=15) -> list[float]:
    """120 dias de tendência suave com ruído (RSI ~50, acima da EMA200),
    queda forte de 8 dias (RSI baixo) e recuperação forte (RSI alto)."""
    n = np.arange(WARMUP)
    trend = list(100 * (1.002 ** n) * (1 + 0.012 * np.sin(n * 1.1)))
    dn = [trend[-1] * drop ** i for i in range(1, drop_days + 1)]
    up = [dn[-1] * rise ** i for i in range(1, rise_days + 1)]
    return trend + dn + up


def signal_days(sig: pd.Series, value: int, start: int = 0) -> list[int]:
    return [i for i, v in enumerate(sig) if v == value and i >= start]


@pytest.fixture
def fake_fetch(monkeypatch):
    def _install(df):
        monkeypatch.setattr(engine, "_fetch_ohlcv", lambda t, s, e: df)
    return _install


# ---------------------------------------------------------------- strategies

def test_registry_has_four_strategies():
    assert set(STRATEGIES) == {"rsi", "ema_crossover", "combined", "dividend_value"}


def test_rsi_buy_on_oversold_and_sell_on_overbought():
    sig = rsi_strategy(make_df(pullback_series()))
    buys = signal_days(sig, 1)
    sells = signal_days(sig, -1)
    assert buys and all(WARMUP <= i < WARMUP + 8 for i in buys)
    assert sells and min(sells) > max(buys)


def test_rsi_custom_thresholds():
    df = make_df(pullback_series())
    never = rsi_strategy(df, rsi_buy=0.0, rsi_sell=100.0)
    assert (never == 0).all()


def test_ema_crossover_emits_only_on_cross_days():
    c = list(np.linspace(100, 60, 40)) + list(np.linspace(60, 130, 40)) + list(np.linspace(130, 70, 40))
    sig = ema_crossover_strategy(make_df(c))
    buys = signal_days(sig, 1, start=40)
    sells = signal_days(sig, -1, start=80)
    assert buys, "esperava cruzamento de alta na recuperação"
    assert sells, "esperava cruzamento de baixa na queda final"
    assert min(buys) < min(sells)
    assert set(sig.unique()) <= {-1, 0, 1}
    # sinal pontual: nunca em dias consecutivos iguais
    assert not any(sig.iloc[i] == sig.iloc[i + 1] != 0 for i in range(len(sig) - 1))


def test_combined_buys_oversold_above_ema200_and_sells_overbought():
    sig = combined_strategy(make_df(pullback_series()))
    buys = signal_days(sig, 1)
    assert buys and all(WARMUP <= i < WARMUP + 8 for i in buys)
    assert min(signal_days(sig, -1, start=min(buys))) > max(buys)


def test_combined_blocks_buy_below_ema200():
    # Queda contínua: RSI muito baixo, mas preço sempre abaixo da EMA200 -> nunca compra.
    c = [100 * 0.99 ** i for i in range(120)]
    sig = combined_strategy(make_df(c))
    assert 1 not in set(sig)


def test_dividend_value_buys_on_5d_drop_and_sells_on_rsi_recovery():
    sig = dividend_value_strategy(make_df(pullback_series()))
    buys = signal_days(sig, 1)
    assert buys and all(WARMUP <= i < WARMUP + 8 for i in buys)
    assert min(signal_days(sig, -1, start=max(buys))) > max(buys)


# -------------------------------------------------------------------- engine

@pytest.mark.parametrize("name", ["rsi", "combined", "dividend_value"])
def test_engine_buy_and_sell_by_strategy(fake_fetch, name):
    fake_fetch(make_df(pullback_series()))
    r = engine.run_simulation("PETR4", "2025-01-01", "2026-01-01", strategy=name)
    actions = [t.action for t in r.trades]
    assert actions[0] == "buy"
    assert "sell" in actions
    first_sell = next(t for t in r.trades if t.action == "sell")
    assert first_sell.reason == name
    assert r.final_capital > r.initial_capital  # comprou na queda, vendeu na alta
    assert r.final_portfolio == []
    assert r.winning_trades >= 1


def test_engine_ema_crossover_trades(fake_fetch):
    c = list(np.linspace(100, 60, 40)) + list(np.linspace(60, 130, 40)) + list(np.linspace(130, 70, 40))
    fake_fetch(make_df(c))
    r = engine.run_simulation(
        "PETR4", "2025-01-01", "2026-01-01", strategy="ema_crossover",
        stop_loss_pct=0.99, take_profit_pct=9.0,  # desliga exits de preço
    )
    assert [t.action for t in r.trades][:2] == ["buy", "sell"]
    assert all(t.reason == "ema_crossover" for t in r.trades)


@pytest.fixture
def scripted(monkeypatch):
    """Estratégia fake: compra no dia 1, nunca vende."""
    def strat(df):
        s = pd.Series(0, index=df.index, dtype=int)
        s.iloc[1] = 1
        return s
    monkeypatch.setitem(STRATEGIES, "scripted", strat)
    return "scripted"


def _run_scripted(fake_fetch, scripted, prices, **kw):
    fake_fetch(make_df(prices))
    return engine.run_simulation("PETR4", "2025-01-01", "2026-01-01", strategy=scripted, **kw)


def test_stop_loss_at_minus_8_percent(fake_fetch, scripted):
    r = _run_scripted(fake_fetch, scripted, [100, 100, 95, 91.9, 90])
    assert [t.action for t in r.trades] == ["buy", "sell"]
    sell = r.trades[1]
    assert sell.price == 91.9
    assert sell.reason.startswith("stop-loss")
    assert r.losing_trades == 1 and r.final_portfolio == []


def test_stop_loss_boundary_exactly_minus_8_triggers(fake_fetch, scripted):
    r = _run_scripted(fake_fetch, scripted, [100, 100, 92.0, 100])
    assert r.trades[1].reason.startswith("stop-loss")


def test_no_stop_above_minus_8(fake_fetch, scripted):
    r = _run_scripted(fake_fetch, scripted, [100, 100, 92.5, 93.0])
    assert [t.action for t in r.trades] == ["buy"]
    assert len(r.final_portfolio) == 1  # posição aberta liquidada ao fim


def test_take_profit_at_plus_20_percent(fake_fetch, scripted):
    r = _run_scripted(fake_fetch, scripted, [100, 100, 110, 121, 150])
    assert [t.action for t in r.trades] == ["buy", "sell"]
    assert r.trades[1].price == 121
    assert r.trades[1].reason.startswith("take-profit")
    assert r.winning_trades == 1
    assert r.final_capital == pytest.approx(10_000 * 1.21, rel=1e-3)


def test_take_profit_boundary_exactly_plus_20_triggers(fake_fetch, scripted):
    r = _run_scripted(fake_fetch, scripted, [100, 100, 120.0, 130])
    assert r.trades[1].reason.startswith("take-profit")


def test_no_take_profit_below_20(fake_fetch, scripted):
    r = _run_scripted(fake_fetch, scripted, [100, 100, 119.9, 119.0])
    assert [t.action for t in r.trades] == ["buy"]


def test_custom_stop_and_take_profit_params(fake_fetch, scripted):
    r = _run_scripted(fake_fetch, scripted, [100, 100, 97], stop_loss_pct=0.02)
    assert r.trades[1].reason.startswith("stop-loss")


def test_max_drawdown_helper():
    assert engine._max_drawdown([100, 120, 90, 110]) == pytest.approx(25.0)
    assert engine._max_drawdown([100, 110, 120]) == 0.0


def test_to_yf_ticker():
    assert engine._to_yf_ticker("petr4") == "PETR4.SA"
    assert engine._to_yf_ticker("PETR4.SA") == "PETR4.SA"
    assert engine._to_yf_ticker("AAPL") == "AAPL"


def test_unknown_strategy_falls_back_to_combined(fake_fetch):
    fake_fetch(make_df(pullback_series()))
    r = engine.run_simulation("PETR4", "2025-01-01", "2026-01-01", strategy="nao_existe")
    assert r.strategy == "nao_existe"
    assert r.trades and r.trades[0].reason == "nao_existe"
