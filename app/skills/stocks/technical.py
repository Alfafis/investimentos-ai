"""
technical_pattern_detector — RSI, MACD, Bollinger Bands, EMA 9/21/200,
candlestick patterns (hammer, doji), overall signal with confidence score.

All math is pure numpy/pandas — no talib dependency.
"""
import asyncio
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf

from app.models import TechnicalSignal
from app.simulation.engine import _to_yf_ticker

_ANNUALIZE = 252


def _fetch_close(ticker: str, period: str = "1y") -> pd.DataFrame:
    sym = _to_yf_ticker(ticker)
    df = yf.download(sym, period=period, auto_adjust=True, progress=False)
    if df.empty:
        raise ValueError(f"No OHLCV data for {ticker}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    return df


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _ema(close: pd.Series, period: int) -> pd.Series:
    return close.ewm(span=period, adjust=False).mean()


def _macd(close: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Returns (macd_line, signal_line, histogram)."""
    ema12 = _ema(close, 12)
    ema26 = _ema(close, 26)
    macd_line = ema12 - ema26
    signal_line = _ema(macd_line, 9)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def _bollinger(close: pd.Series, period: int = 20, std_mult: float = 2.0) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Returns (upper, mid, lower)."""
    mid = close.rolling(period).mean()
    std = close.rolling(period).std()
    return mid + std_mult * std, mid, mid - std_mult * std


def _detect_candlestick(df: pd.DataFrame) -> Optional[str]:
    """Check last 1-2 candles for simple patterns."""
    if len(df) < 2:
        return None

    last = df.iloc[-1]
    prev = df.iloc[-2]
    o, h, l, c = last["Open"], last["High"], last["Low"], last["Close"]
    body = abs(c - o)
    full_range = h - l
    if full_range == 0:
        return None

    # Doji: body < 10% of range
    if body / full_range < 0.10:
        return "doji"

    # Hammer: small body at top, long lower wick (bullish reversal)
    lower_wick = min(o, c) - l
    upper_wick = h - max(o, c)
    if lower_wick > 2 * body and upper_wick < 0.3 * body:
        return "hammer"

    # Shooting star: small body at bottom, long upper wick (bearish)
    if upper_wick > 2 * body and lower_wick < 0.3 * body:
        return "shooting_star"

    # Engulfing bullish
    prev_o, prev_c = prev["Open"], prev["Close"]
    if prev_c < prev_o and c > o and c > prev_o and o < prev_c:
        return "bullish_engulfing"

    # Engulfing bearish
    if prev_c > prev_o and c < o and c < prev_o and o > prev_c:
        return "bearish_engulfing"

    return None


def detect_patterns(ticker: str, period: str = "1y", df: Optional[pd.DataFrame] = None) -> TechnicalSignal:
    """
    Compute technical indicators and derive buy/sell/hold signal.

    Args:
        ticker: B3 symbol, e.g. "PETR4"
        period: yfinance period — "3mo", "6mo", "1y"
        df: pre-fetched OHLCV DataFrame (skips yfinance download when provided)

    Returns:
        TechnicalSignal with indicators, signal, confidence, and reasons
    """
    if df is None:
        df = _fetch_close(ticker, period)
    close = df["Close"]

    rsi = _rsi(close)
    ema9 = _ema(close, 9)
    ema21 = _ema(close, 21)
    ema200 = _ema(close, 200)
    macd_line, macd_sig, macd_hist = _macd(close)
    bb_upper, bb_mid, bb_lower = _bollinger(close)
    candle = _detect_candlestick(df)

    # Current values (last row)
    cur_rsi = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None
    cur_ema9 = float(ema9.iloc[-1])
    cur_ema21 = float(ema21.iloc[-1])
    cur_ema200 = float(ema200.iloc[-1]) if len(close) >= 200 else None
    cur_macd = float(macd_line.iloc[-1])
    cur_macd_sig = float(macd_sig.iloc[-1])
    cur_macd_hist = float(macd_hist.iloc[-1])
    cur_bb_upper = float(bb_upper.iloc[-1])
    cur_bb_mid = float(bb_mid.iloc[-1])
    cur_bb_lower = float(bb_lower.iloc[-1])
    cur_price = float(close.iloc[-1])

    # Volume indicators
    vol_last: Optional[int] = None
    vol_avg_20d: Optional[float] = None
    vol_ratio: Optional[float] = None
    if "Volume" in df.columns:
        volume = df["Volume"].dropna()
        if not volume.empty:
            vol_last = int(volume.iloc[-1])
            avg = volume.rolling(20).mean().iloc[-1]
            if not pd.isna(avg) and avg > 0:
                vol_avg_20d = round(float(avg), 0)
                vol_ratio = round(vol_last / vol_avg_20d, 2)

    bullish = 0
    bearish = 0
    reasons: list[str] = []

    # RSI
    if cur_rsi is not None:
        if cur_rsi < 30:
            bullish += 2
            reasons.append(f"RSI oversold ({cur_rsi:.1f})")
        elif cur_rsi < 40:
            bullish += 1
            reasons.append(f"RSI approaching oversold ({cur_rsi:.1f})")
        elif cur_rsi > 70:
            bearish += 2
            reasons.append(f"RSI overbought ({cur_rsi:.1f})")
        elif cur_rsi > 60:
            bearish += 1
            reasons.append(f"RSI approaching overbought ({cur_rsi:.1f})")

    # EMA 9/21 crossover
    if cur_ema9 > cur_ema21:
        bullish += 1
        reasons.append("EMA9 above EMA21 (golden cross)")
    else:
        bearish += 1
        reasons.append("EMA9 below EMA21 (death cross)")

    # Price vs EMA200
    if cur_ema200 is not None:
        if cur_price > cur_ema200:
            bullish += 1
            reasons.append("Price above EMA200 (uptrend)")
        else:
            bearish += 1
            reasons.append("Price below EMA200 (downtrend)")

    # MACD histogram direction
    if cur_macd_hist > 0:
        bullish += 1
        reasons.append("MACD histogram positive")
    else:
        bearish += 1
        reasons.append("MACD histogram negative")

    # Bollinger Bands
    if cur_price < cur_bb_lower:
        bullish += 1
        reasons.append("Price below lower Bollinger Band (oversold)")
    elif cur_price > cur_bb_upper:
        bearish += 1
        reasons.append("Price above upper Bollinger Band (overbought)")

    # Candlestick patterns
    if candle in ("hammer", "bullish_engulfing"):
        bullish += 1
        reasons.append(f"Candlestick: {candle}")
    elif candle in ("shooting_star", "bearish_engulfing"):
        bearish += 1
        reasons.append(f"Candlestick: {candle}")

    total = bullish + bearish
    confidence = round(max(bullish, bearish) / total, 3) if total > 0 else 0.5

    if bullish > bearish:
        signal = "buy"
    elif bearish > bullish:
        signal = "sell"
    else:
        signal = "hold"

    return TechnicalSignal(
        ticker=ticker,
        timestamp=datetime.now(timezone.utc).isoformat(),
        rsi_14=round(cur_rsi, 2) if cur_rsi is not None else None,
        macd=round(cur_macd, 4),
        macd_signal=round(cur_macd_sig, 4),
        macd_hist=round(cur_macd_hist, 4),
        ema_9=round(cur_ema9, 2),
        ema_21=round(cur_ema21, 2),
        ema_200=round(cur_ema200, 2) if cur_ema200 else None,
        bb_upper=round(cur_bb_upper, 2),
        bb_mid=round(cur_bb_mid, 2),
        bb_lower=round(cur_bb_lower, 2),
        candlestick_pattern=candle,
        volume_last=vol_last,
        volume_avg_20d=vol_avg_20d,
        volume_ratio_20d=vol_ratio,
        signal=signal,
        confidence=confidence,
        reasons=reasons,
    )


async def detect_patterns_async(ticker: str, period: str = "1y", df: Optional[pd.DataFrame] = None) -> TechnicalSignal:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: detect_patterns(ticker, period, df))
