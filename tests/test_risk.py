import math

import numpy as np
import pandas as pd
import pytest

from app.skills.shared import risk


def test_max_drawdown_known_series():
    r = pd.Series([0.10, -0.10, 0.10, -0.20])
    # equity 1.1, 0.99, 1.089, 0.8712 ; pico 1.1 -> vale 0.8712 = queda de 20.8%
    assert risk._max_drawdown(r) == pytest.approx(20.8)


def test_max_drawdown_monotonic_up_is_zero():
    assert risk._max_drawdown(pd.Series([0.01, 0.02, 0.03])) == 0.0


def test_var_historical_percentile():
    r = pd.Series(np.arange(-50, 50) / 1000.0)  # -5% .. +4.9%
    expected = abs(np.percentile(r, 5))
    assert risk._var(r, 0.95) == pytest.approx(expected)
    assert risk._var(r, 0.95) == pytest.approx(0.04505, abs=1e-6)
    assert risk._var(r, 0.99) > risk._var(r, 0.95)


def test_var_all_positive_returns_is_absolute_of_percentile():
    # documenta o comportamento: abs() do percentil, mesmo quando não há perda
    r = pd.Series([0.01] * 100)
    assert risk._var(r) == pytest.approx(0.01)


def test_sharpe_known_series():
    r = pd.Series([0.01, -0.005] * 50)
    rf = (1 + 0.105) ** (1 / 252) - 1
    ex = r - rf
    expected = ex.mean() / ex.std() * math.sqrt(252)
    assert risk._sharpe(r) == pytest.approx(expected)
    assert risk._sharpe(r) > 0


def test_sharpe_zero_risk_free_hand_computed():
    r = pd.Series([0.02, 0.0, 0.02, 0.0])  # mean .01, std(ddof=1)=0.011547
    assert risk._sharpe(r, risk_free_annual=0.0) == pytest.approx(
        0.01 / 0.0115470054 * math.sqrt(252), rel=1e-6
    )


def test_sharpe_constant_returns_is_zero():
    rf = (1 + 0.105) ** (1 / 252) - 1
    assert risk._sharpe(pd.Series([rf] * 10)) == 0.0


def test_sharpe_below_risk_free_is_negative():
    assert risk._sharpe(pd.Series([0.0001, -0.0001] * 50)) < 0


def test_sortino_ignores_upside_volatility():
    r = pd.Series([0.05, 0.001, -0.01, 0.04, -0.02, 0.03])
    assert risk._sortino(r) > risk._sharpe(r)


def test_sortino_without_downside_is_zero():
    assert risk._sortino(pd.Series([0.01, 0.02, 0.03])) == 0.0


def test_kelly_capped_and_floored():
    assert risk._kelly_fraction(pd.Series([0.01, 0.02, 0.015])) == 0.10  # teto
    assert risk._kelly_fraction(pd.Series([-0.01, -0.02, -0.015])) == 0.0
    assert risk._kelly_fraction(pd.Series([0.01, 0.01])) == 0.0  # variância zero


def test_beta_of_scaled_market_is_scale():
    rng = np.random.default_rng(0)
    m = pd.Series(rng.normal(0, 0.01, 100))
    assert risk._beta(m * 1.5, m) == pytest.approx(1.5)
    assert risk._beta(m.iloc[:10], m.iloc[:10]) == 1.0  # amostra curta -> default


def test_calculate_risk_end_to_end_with_mocked_download(monkeypatch):
    idx = pd.bdate_range("2025-01-02", periods=60)
    closes = pd.Series(100 * np.cumprod(1 + np.tile([0.01, -0.004, 0.006], 20)), index=idx)
    df = pd.DataFrame({"Close": closes})
    monkeypatch.setattr(risk.yf, "download", lambda *a, **k: df.copy())
    m = risk.calculate_risk("PETR4")
    ret = closes.pct_change().dropna()
    assert m.max_drawdown == pytest.approx(round(risk._max_drawdown(ret), 2))
    assert m.var_95 == pytest.approx(round(risk._var(ret) * 100, 3))
    assert m.sharpe_ratio == pytest.approx(round(risk._sharpe(ret), 3))
    assert m.beta == pytest.approx(1.0, abs=1e-2)  # mesmo df como mercado
    assert m.var_99 >= m.var_95


def test_calculate_risk_empty_data_raises(monkeypatch):
    monkeypatch.setattr(risk.yf, "download", lambda *a, **k: pd.DataFrame())
    with pytest.raises(ValueError):
        risk.calculate_risk("PETR4")
