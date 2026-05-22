"""
risk_calculator — VaR, Sharpe, Sortino, beta, drawdown, Kelly Criterion.
circuit_breaker  — daily/weekly loss threshold check.
correlation_matrix — pairwise asset correlation.

All calculations are deterministic Python/numpy — never delegated to LLM.
"""
import asyncio
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf

from app.models import CircuitBreakerResult, CorrelationResult, RiskMetrics
from app.simulation.engine import _to_yf_ticker

_MARKET_TICKER = "^BVSP"
_ANNUALIZE = 252  # trading days


def _fetch_returns(ticker: str, period: str = "1y") -> pd.Series:
    sym = _to_yf_ticker(ticker)
    df = yf.download(sym, period=period, auto_adjust=True, progress=False)
    if df.empty:
        raise ValueError(f"No data for {ticker}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    return df["Close"].pct_change().dropna()


def _kelly_fraction(returns: pd.Series, cap: float = 0.10) -> float:
    """
    Simplified continuous Kelly: f* = μ / σ²
    Capped at `cap` (default 10%) to prevent extreme sizing.
    """
    mu = returns.mean()
    sigma2 = returns.var()
    if sigma2 == 0:
        return 0.0
    kelly = mu / sigma2
    return round(min(max(kelly, 0.0), cap), 4)


def _var(returns: pd.Series, confidence: float = 0.95) -> float:
    """Historical VaR (negative return at percentile)."""
    return float(abs(np.percentile(returns, (1 - confidence) * 100)))


def _max_drawdown(returns: pd.Series) -> float:
    equity = (1 + returns).cumprod()
    rolling_max = equity.cummax()
    drawdown = (equity - rolling_max) / rolling_max
    return float(abs(drawdown.min()) * 100)


def _beta(asset_returns: pd.Series, market_returns: pd.Series) -> float:
    aligned = pd.concat([asset_returns, market_returns], axis=1).dropna()
    if aligned.empty or len(aligned) < 20:
        return 1.0
    cov = np.cov(aligned.iloc[:, 0], aligned.iloc[:, 1])
    return float(cov[0, 1] / cov[1, 1]) if cov[1, 1] != 0 else 1.0


def _sharpe(returns: pd.Series, risk_free_annual: float = 0.105) -> float:
    """Annualized Sharpe. risk_free_annual = Selic approximation."""
    rf_daily = (1 + risk_free_annual) ** (1 / _ANNUALIZE) - 1
    excess = returns - rf_daily
    if excess.std() == 0:
        return 0.0
    return float(excess.mean() / excess.std() * np.sqrt(_ANNUALIZE))


def _sortino(returns: pd.Series, risk_free_annual: float = 0.105) -> float:
    rf_daily = (1 + risk_free_annual) ** (1 / _ANNUALIZE) - 1
    excess = returns - rf_daily
    downside = excess[excess < 0].std()
    if downside == 0:
        return 0.0
    return float(excess.mean() / downside * np.sqrt(_ANNUALIZE))


def calculate_risk(
    ticker: str,
    period: str = "1y",
    risk_free_annual: float = 0.105,
) -> RiskMetrics:
    """
    Full risk profile for a B3 stock.

    Args:
        ticker: B3 symbol, e.g. "PETR4"
        period: yfinance period string — "1y", "2y", "6mo", etc.
        risk_free_annual: Annual risk-free rate (defaults to ~Selic 10.5%)
    """
    asset_ret = _fetch_returns(ticker, period)
    df_mkt = yf.download(_MARKET_TICKER, period=period, auto_adjust=True, progress=False)
    if isinstance(df_mkt.columns, pd.MultiIndex):
        df_mkt.columns = df_mkt.columns.droplevel(1)
    market_ret = df_mkt["Close"].pct_change().dropna()

    kelly = _kelly_fraction(asset_ret)
    ann_vol = float(asset_ret.std() * np.sqrt(_ANNUALIZE) * 100)

    return RiskMetrics(
        ticker=ticker,
        period=period,
        var_95=round(_var(asset_ret, 0.95) * 100, 3),
        var_99=round(_var(asset_ret, 0.99) * 100, 3),
        max_drawdown=round(_max_drawdown(asset_ret), 2),
        sharpe_ratio=round(_sharpe(asset_ret, risk_free_annual), 3),
        sortino_ratio=round(_sortino(asset_ret, risk_free_annual), 3),
        beta=round(_beta(asset_ret, market_ret), 3),
        volatility_annual_pct=round(ann_vol, 2),
        kelly_fraction=kelly,
        kelly_position_pct=round(kelly * 100, 2),
    )


async def calculate_risk_async(ticker: str, period: str = "1y") -> RiskMetrics:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: calculate_risk(ticker, period))


def check_circuit_breaker(
    ticker: str,
    daily_loss_limit_pct: float = 2.0,
    weekly_loss_limit_pct: float = 5.0,
) -> CircuitBreakerResult:
    """
    Check if daily or weekly loss exceeds thresholds.
    Trigger = stop all operations for this ticker.
    """
    sym = _to_yf_ticker(ticker)
    df = yf.download(sym, period="10d", auto_adjust=True, progress=False)
    if df.empty:
        return CircuitBreakerResult(ticker=ticker, triggered=False, reason="no data")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)

    closes = df["Close"].dropna()
    daily_ret = float((closes.iloc[-1] - closes.iloc[-2]) / closes.iloc[-2] * 100)
    weekly_ret = float((closes.iloc[-1] - closes.iloc[-6]) / closes.iloc[-6] * 100) if len(closes) >= 6 else 0.0

    triggered = False
    reason = ""
    if daily_ret <= -daily_loss_limit_pct:
        triggered = True
        reason = f"daily loss {daily_ret:.2f}% exceeds -{daily_loss_limit_pct}% limit"
    elif weekly_ret <= -weekly_loss_limit_pct:
        triggered = True
        reason = f"weekly loss {weekly_ret:.2f}% exceeds -{weekly_loss_limit_pct}% limit"

    return CircuitBreakerResult(
        ticker=ticker,
        triggered=triggered,
        reason=reason,
        daily_return_pct=round(daily_ret, 2),
        weekly_return_pct=round(weekly_ret, 2),
    )


def correlation_matrix(tickers: list[str], period: str = "1y") -> CorrelationResult:
    """
    Compute pairwise Pearson correlation between assets.
    Flags pairs with |corr| > 0.7 as high-correlation risk.
    """
    returns = {}
    for t in tickers:
        try:
            returns[t] = _fetch_returns(t, period)
        except Exception:
            pass

    if not returns:
        return CorrelationResult(tickers=tickers, matrix={}, high_correlation_pairs=[])

    df = pd.DataFrame(returns).dropna()
    corr = df.corr().round(3)

    high_pairs = []
    for i, a in enumerate(corr.columns):
        for b in corr.columns[i + 1:]:
            val = float(corr.loc[a, b])
            if abs(val) >= 0.7:
                high_pairs.append({"pair": [a, b], "correlation": val})

    return CorrelationResult(
        tickers=list(returns.keys()),
        matrix=corr.to_dict(),
        high_correlation_pairs=high_pairs,
    )
