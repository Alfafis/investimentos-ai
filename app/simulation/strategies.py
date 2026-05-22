"""
Investment / disinvestment criteria.

Each strategy receives a DataFrame with OHLCV columns and returns a pd.Series
with values: 1 (buy signal), -1 (sell signal), 0 (hold).

Rules are evaluated daily. The engine handles position state — strategies
only need to emit signals; they don't need to track open/closed positions.
"""
import pandas as pd
import numpy as np


def _rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _ema(prices: pd.Series, period: int) -> pd.Series:
    return prices.ewm(span=period, adjust=False).mean()


# ---------------------------------------------------------------------------
# Strategy 1 — Pure RSI
# Buy criterion:  RSI < 30 (oversold)
# Sell criterion: RSI > 70 (overbought)
# ---------------------------------------------------------------------------
def rsi_strategy(df: pd.DataFrame, rsi_buy: float = 30.0, rsi_sell: float = 70.0) -> pd.Series:
    rsi = _rsi(df["Close"])
    signal = pd.Series(0, index=df.index, dtype=int)
    signal[rsi < rsi_buy] = 1
    signal[rsi > rsi_sell] = -1
    return signal


# ---------------------------------------------------------------------------
# Strategy 2 — EMA Crossover (9 / 21)
# Buy criterion:  fast EMA crosses above slow EMA
# Sell criterion: fast EMA crosses below slow EMA
# Signals emitted only on crossover day (not continuously).
# ---------------------------------------------------------------------------
def ema_crossover_strategy(df: pd.DataFrame, fast: int = 9, slow: int = 21) -> pd.Series:
    fast_ema = _ema(df["Close"], fast)
    slow_ema = _ema(df["Close"], slow)
    position = (fast_ema > slow_ema).astype(int).replace(0, -1)
    # diff gives +2 on bullish cross, -2 on bearish — map to 1/-1/0
    cross = position.diff()
    signal = pd.Series(0, index=df.index, dtype=int)
    signal[cross > 0] = 1
    signal[cross < 0] = -1
    return signal


# ---------------------------------------------------------------------------
# Strategy 3 — Combined (recommended)
# Buy criterion:  RSI < 35 AND price above 200-day EMA (trend filter)
# Sell criterion: RSI > 65 OR dividend yield < 3% (use RSI for simplicity)
#
# Additional exit rules are handled at the engine level:
#   - Stop-loss: -8%
#   - Take-profit: +20%
#   - Trailing stop (optional, engine param)
# ---------------------------------------------------------------------------
def combined_strategy(df: pd.DataFrame) -> pd.Series:
    rsi = _rsi(df["Close"])
    ema200 = _ema(df["Close"], 200)

    signal = pd.Series(0, index=df.index, dtype=int)
    buy_cond = (rsi < 35) & (df["Close"] > ema200)
    sell_cond = rsi > 65

    signal[buy_cond] = 1
    signal[sell_cond] = -1
    return signal


# ---------------------------------------------------------------------------
# Strategy 4 — Dividend + Value (FII / high-yield stocks)
# Buy criterion:  price dropped > 5% in 5 days AND RSI < 40
# Sell criterion: price recovered to entry + 15% OR RSI > 60
# ---------------------------------------------------------------------------
def dividend_value_strategy(df: pd.DataFrame) -> pd.Series:
    rsi = _rsi(df["Close"])
    pct_5d = df["Close"].pct_change(5) * 100

    signal = pd.Series(0, index=df.index, dtype=int)
    buy_cond = (pct_5d < -5) & (rsi < 40)
    sell_cond = rsi > 60

    signal[buy_cond] = 1
    signal[sell_cond] = -1
    return signal


STRATEGIES: dict[str, callable] = {
    "rsi": rsi_strategy,
    "ema_crossover": ema_crossover_strategy,
    "combined": combined_strategy,
    "dividend_value": dividend_value_strategy,
}
