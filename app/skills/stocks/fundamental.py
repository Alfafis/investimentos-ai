"""
fundamental_analyzer — earnings parsing, DCF valuation, peer comparison.

Data source: yfinance (free, no key). All financials in BRL.
DCF uses simplified Gordon-Growth model with configurable WACC.
"""
import asyncio
from typing import Optional

import yfinance as yf

from app.models import FundamentalMetrics, PeerComparison
from app.simulation.engine import _to_yf_ticker


def _safe_float(val) -> Optional[float]:
    try:
        v = float(val)
        return None if (v != v) else round(v, 4)  # NaN check
    except (TypeError, ValueError):
        return None


def parse_quarterly_earnings(ticker: str) -> FundamentalMetrics:
    """
    Pull key fundamental metrics from yfinance.

    Returns P/E, P/B, ROE, EV/EBITDA, revenue growth YoY,
    net margin, D/E ratio, dividend yield, and DCF fair value estimate.
    """
    sym = _to_yf_ticker(ticker)
    info = yf.Ticker(sym).info

    pe = _safe_float(info.get("trailingPE"))
    pb = _safe_float(info.get("priceToBook"))
    roe = _safe_float(info.get("returnOnEquity"))
    if roe is not None:
        roe = round(roe * 100, 2)  # convert to %

    ev_ebitda = _safe_float(info.get("enterpriseToEbitda"))
    revenue_growth = _safe_float(info.get("revenueGrowth"))
    if revenue_growth is not None:
        revenue_growth = round(revenue_growth * 100, 2)

    net_margin = _safe_float(info.get("profitMargins"))
    if net_margin is not None:
        net_margin = round(net_margin * 100, 2)

    debt_equity = _safe_float(info.get("debtToEquity"))
    dividend_yield = _safe_float(info.get("dividendYield"))
    if dividend_yield is not None:
        dividend_yield = round(dividend_yield * 100, 2)

    current_price = _safe_float(info.get("currentPrice") or info.get("regularMarketPrice"))

    avg_volume = info.get("averageDailyVolume10Day") or info.get("averageVolume")
    avg_volume_10d = int(avg_volume) if avg_volume else None
    market_cap = _safe_float(info.get("marketCap"))

    # Simplified DCF: P = EPS * (1 + g) / (WACC - g)
    # Uses trailing EPS, assumes 5% perpetual growth, 12% WACC (Brazil risk premium)
    dcf_fair_value = None
    upside_pct = None
    eps = _safe_float(info.get("trailingEps"))
    if eps and eps > 0:
        g = 0.05
        wacc = 0.12
        if wacc > g:
            dcf_fair_value = round(eps * (1 + g) / (wacc - g), 2)
            if current_price and current_price > 0:
                upside_pct = round((dcf_fair_value - current_price) / current_price * 100, 2)

    return FundamentalMetrics(
        ticker=ticker,
        pe_ratio=pe,
        pb_ratio=pb,
        roe=roe,
        ev_ebitda=ev_ebitda,
        revenue_growth_yoy=revenue_growth,
        net_margin=net_margin,
        debt_equity=debt_equity,
        dividend_yield=dividend_yield,
        dcf_fair_value=dcf_fair_value,
        current_price=current_price,
        upside_pct=upside_pct,
        avg_volume_10d=avg_volume_10d,
        market_cap_brl=market_cap,
    )


def dcf_valuation(
    ticker: str,
    wacc: float = 0.12,
    growth_rate: float = 0.05,
) -> dict:
    """
    Explicit DCF with configurable WACC and perpetual growth rate.

    Returns fair_value, current_price, upside_pct, inputs used.
    """
    sym = _to_yf_ticker(ticker)
    info = yf.Ticker(sym).info
    eps = _safe_float(info.get("trailingEps"))
    current_price = _safe_float(info.get("currentPrice") or info.get("regularMarketPrice"))

    if not eps or eps <= 0:
        return {"error": "No positive EPS available for DCF", "ticker": ticker}

    if wacc <= growth_rate:
        return {"error": "WACC must be greater than growth_rate", "ticker": ticker}

    fair_value = round(eps * (1 + growth_rate) / (wacc - growth_rate), 2)
    upside = round((fair_value - current_price) / current_price * 100, 2) if current_price else None

    return {
        "ticker": ticker,
        "fair_value": fair_value,
        "current_price": current_price,
        "upside_pct": upside,
        "inputs": {"eps": eps, "wacc": wacc, "growth_rate": growth_rate},
    }


def peer_comparison(ticker: str, peers: list[str]) -> PeerComparison:
    """
    Compare ticker against peers on P/E, P/B, ROE, EV/EBITDA.

    Returns matrix with all tickers including the target.
    """
    all_tickers = [ticker] + [p for p in peers if p != ticker]
    metrics_map: dict[str, dict] = {}

    for t in all_tickers:
        try:
            m = parse_quarterly_earnings(t)
            metrics_map[t] = {
                "pe_ratio": m.pe_ratio,
                "pb_ratio": m.pb_ratio,
                "roe": m.roe,
                "ev_ebitda": m.ev_ebitda,
                "dividend_yield": m.dividend_yield,
                "net_margin": m.net_margin,
            }
        except Exception:
            metrics_map[t] = {}

    return PeerComparison(ticker=ticker, peers=peers, metrics=metrics_map)


async def parse_quarterly_earnings_async(ticker: str) -> FundamentalMetrics:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: parse_quarterly_earnings(ticker))


async def peer_comparison_async(ticker: str, peers: list[str]) -> PeerComparison:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: peer_comparison(ticker, peers))
