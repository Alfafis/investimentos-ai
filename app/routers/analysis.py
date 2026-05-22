"""
/analysis — REST endpoints for risk, technical, fundamental, macro, sentiment, portfolio.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.models import PortfolioInput, PortfolioPosition
from app.skills.shared.macro import load_macro_context
from app.skills.shared.risk import calculate_risk_async, check_circuit_breaker, correlation_matrix
from app.skills.shared.portfolio import track_portfolio
from app.skills.shared.sentiment import analyze_sentiment
from app.skills.stocks.technical import detect_patterns_async
from app.skills.stocks.fundamental import (
    parse_quarterly_earnings_async,
    peer_comparison_async,
    dcf_valuation,
)

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/macro")
async def macro():
    """Current macro context: Selic, IPCA, USD/BRL, Ibovespa, market status."""
    ctx = await load_macro_context()
    return ctx.model_dump()


@router.get("/risk/{ticker}")
async def risk(
    ticker: str,
    period: str = Query("1y", description="yfinance period: 6mo, 1y, 2y"),
    risk_free_annual: float = Query(0.105, description="Annual risk-free rate"),
):
    """Risk metrics: VaR, Sharpe, Sortino, beta, Kelly for a B3 ticker."""
    try:
        result = await calculate_risk_async(ticker.upper(), period)
        return result.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/circuit-breaker/{ticker}")
def circuit_breaker(
    ticker: str,
    daily_limit: float = Query(2.0, description="Daily loss % to trigger halt"),
    weekly_limit: float = Query(5.0, description="Weekly loss % to trigger halt"),
):
    """Check if ticker breached circuit breaker thresholds."""
    result = check_circuit_breaker(ticker.upper(), daily_limit, weekly_limit)
    return result.model_dump()


@router.get("/correlation")
def correlation(
    tickers: str = Query(..., description="Comma-separated B3 symbols, e.g. PETR4,VALE3"),
    period: str = Query("1y"),
):
    """Pairwise Pearson correlation matrix. Flags |corr| >= 0.7 as high risk."""
    ticker_list = [t.strip().upper() for t in tickers.split(",")]
    result = correlation_matrix(ticker_list, period)
    return result.model_dump()


@router.get("/technical/{ticker}")
async def technical(
    ticker: str,
    period: str = Query("6mo", description="Data window: 3mo, 6mo, 1y"),
):
    """Technical analysis: RSI, MACD, EMA, Bollinger Bands, candlestick patterns."""
    try:
        result = await detect_patterns_async(ticker.upper(), period)
        return result.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/fundamental/{ticker}")
async def fundamental(ticker: str):
    """Fundamental metrics: P/E, P/B, ROE, EV/EBITDA, DCF fair value."""
    try:
        result = await parse_quarterly_earnings_async(ticker.upper())
        return result.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dcf/{ticker}")
def dcf(
    ticker: str,
    wacc: float = Query(0.12, description="Weighted avg cost of capital"),
    growth_rate: float = Query(0.05, description="Perpetual earnings growth rate"),
):
    """Simplified DCF: P = EPS × (1+g) / (WACC−g)."""
    return dcf_valuation(ticker.upper(), wacc, growth_rate)


@router.get("/peers/{ticker}")
async def peers(
    ticker: str,
    peer_list: str = Query(..., alias="peers", description="Comma-separated peer tickers"),
):
    """Compare ticker vs peers on fundamental multiples."""
    peers_parsed = [p.strip().upper() for p in peer_list.split(",")]
    result = await peer_comparison_async(ticker.upper(), peers_parsed)
    return result.model_dump()


@router.get("/sentiment/{ticker}")
async def sentiment(
    ticker: str,
    max_articles: int = Query(10, ge=1, le=30),
):
    """PT-BR news sentiment from InfoMoney + Investing.com BR RSS feeds."""
    result = await analyze_sentiment(ticker.upper(), max_articles)
    return result.model_dump()


class PortfolioRequest(BaseModel):
    positions: list[dict]
    cash: float = 0.0


@router.post("/portfolio")
async def portfolio(body: PortfolioRequest):
    """
    Current portfolio P&L, sector exposure, top/worst performer.

    Body: {"positions": [{"ticker": "PETR4", "quantity": 100, "avg_price": 35.50}], "cash": 1000}
    """
    try:
        parsed = [
            PortfolioPosition(
                ticker=p["ticker"].upper(),
                quantity=p["quantity"],
                avg_price=p["avg_price"],
            )
            for p in body.positions
        ]
        inp = PortfolioInput(positions=parsed, cash=body.cash)
        summary = await track_portfolio(inp)
        return summary.model_dump()
    except (KeyError, TypeError) as e:
        raise HTTPException(status_code=422, detail=f"Invalid position data: {e}")
