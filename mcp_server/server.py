"""
MCP server for Investimentos AI.

Exposes B3 stock quotes and investment simulation as Claude tools.

Run locally (stdio, for Claude Desktop):
    python -m mcp_server.server

Run as HTTP server (for network/Docker use):
    python -m mcp_server.server --transport streamable-http --port 8001
"""
import sys
from typing import Optional

from mcp.server.fastmcp import FastMCP

# Ensure app package is importable when running mcp_server directly
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.quotes.client import get_quotes
from app.simulation.engine import run_simulation
from app.simulation.strategies import STRATEGIES
from app.agent.investing_pipeline import run_investing_pipeline
from app.skills.shared.scorer import score_watchlist
from app.skills.shared.macro import load_macro_context
from app.skills.shared.risk import calculate_risk_async, check_circuit_breaker, correlation_matrix
from app.skills.shared.portfolio import track_portfolio
from app.skills.shared.sentiment import analyze_sentiment
from app.skills.stocks.technical import detect_patterns_async
from app.skills.stocks.fundamental import parse_quarterly_earnings_async, peer_comparison_async, dcf_valuation
from app.models import PortfolioInput, PortfolioPosition
from app.experiment.store import (
    save_decision as _save_decision,
    get_decision_log as _get_decision_log,
    save_paper_trade as _save_paper_trade,
    get_paper_portfolio as _get_paper_portfolio,
    get_trade_outcomes as _get_trade_outcomes,
)

import os as _os
_MCP_HOST = _os.environ.get("MCP_HOST", "127.0.0.1")
_MCP_PORT = int(_os.environ.get("MCP_PORT", "8001"))

mcp = FastMCP(
    "investimentos-ai",
    host=_MCP_HOST,
    port=_MCP_PORT,
    instructions=(
        "Financial AI tools for the Brazilian stock market (B3). "
        "Use get_stock_quotes for real-time prices, simulate_investment for backtesting, "
        "and screen_stocks to filter buy candidates."
    ),
)


# ---------------------------------------------------------------------------
# Tool 1 — Real-time quotes (yfinance / Yahoo Finance)
# ---------------------------------------------------------------------------
@mcp.tool()
async def get_stock_quotes(
    tickers: list[str],
    sort: Optional[str] = None,
) -> dict:
    """
    Fetch current B3 stock quotes via Yahoo Finance (yfinance, ~15min delay).

    Args:
        tickers: B3 ticker symbols, e.g. ["PETR4", "VALE3", "ITUB4"]
        sort: Optional sort key — "value:asc", "value:desc", "change_percent:desc", etc.

    Returns:
        List of quotes with price, daily change, market cap, and 12-month dividend yield.
    """
    b3_tickers = [f"B3:{t.strip().upper()}" for t in tickers]
    data = await get_quotes(b3_tickers, sort)
    meta = data.get("metadata") or {}
    results = []
    for item in data.get("results", []):
        q = item.get("quote") or {}
        div = item.get("dividends") or {}
        results.append({
            "ticker": item.get("symbol"),
            "name": item.get("name"),
            "price_brl": q.get("value"),
            "change_pct": q.get("change_percent"),
            "change_value": q.get("change_value"),
            "market_cap": q.get("market_cap"),
            "dividend_yield_12m_pct": div.get("yield_12m_percent"),
            "updated_at": q.get("updated_at"),
        })
    return {
        "quotes": results,
        "count": len(results),
        "cached": meta.get("cached", False),
        "response_time_ms": meta.get("response_time_ms", 0),
    }


# ---------------------------------------------------------------------------
# Tool 2 — Investment simulation / backtesting
# ---------------------------------------------------------------------------
@mcp.tool()
def simulate_investment(
    ticker: str,
    start_date: str,
    end_date: str,
    initial_capital: float = 10_000.0,
    strategy: str = "combined",
    stop_loss_pct: float = 0.08,
    take_profit_pct: float = 0.20,
) -> dict:
    """
    Backtest an investment strategy on a B3 stock using historical data from Yahoo Finance.

    Strategies available:
    - "combined"       : RSI < 35 + above 200 EMA for entry; RSI > 65 for exit (recommended)
    - "rsi"            : Pure RSI — buy RSI < 30, sell RSI > 70
    - "ema_crossover"  : EMA 9/21 — buy on bullish crossover, sell on bearish
    - "dividend_value" : Dip buyer — 5-day drop > 5% + RSI < 40

    Exit rules applied to all strategies regardless of signal:
    - Stop-loss at -stop_loss_pct (default -8%)
    - Take-profit at +take_profit_pct (default +20%)

    Args:
        ticker: B3 ticker symbol, e.g. "PETR4" (auto-appended with .SA for yfinance)
        start_date: Backtest start in YYYY-MM-DD format
        end_date: Backtest end in YYYY-MM-DD format
        initial_capital: Starting capital in BRL
        strategy: Strategy name (see above)
        stop_loss_pct: Stop-loss threshold as decimal, e.g. 0.08 = 8%
        take_profit_pct: Take-profit threshold as decimal, e.g. 0.20 = 20%

    Returns:
        Performance summary and full trade log.
    """
    result = run_simulation(
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital,
        strategy=strategy,
        stop_loss_pct=stop_loss_pct,
        take_profit_pct=take_profit_pct,
    )
    return result.model_dump()


# ---------------------------------------------------------------------------
# Tool 3 — Stock screener
# ---------------------------------------------------------------------------
@mcp.tool()
async def screen_stocks(
    tickers: list[str],
    min_dividend_yield_pct: float = 0.0,
    min_drop_pct: float = 0.0,
) -> dict:
    """
    Screen B3 stocks for buy candidates based on current quotes.

    Filters:
    - min_dividend_yield_pct: Only include stocks with 12-month DY >= this value (e.g. 6.0 = 6%)
    - min_drop_pct: Only include stocks down at least this % today (e.g. 2.0 = -2% or worse)

    Args:
        tickers: List of B3 ticker symbols to screen
        min_dividend_yield_pct: Minimum 12-month dividend yield percentage
        min_drop_pct: Minimum today's drop percentage (positive number means "down at least X%")

    Returns:
        Filtered candidates sorted by dividend yield descending.
    """
    b3_tickers = [f"B3:{t.strip().upper()}" for t in tickers]
    data = await get_quotes(b3_tickers)

    candidates = []
    for item in data.get("results", []):
        q = item.get("quote") or {}
        div = item.get("dividends") or {}
        dy = div.get("yield_12m_percent") or 0.0
        change_pct = q.get("change_percent") or 0.0

        if dy < min_dividend_yield_pct:
            continue
        if min_drop_pct > 0 and change_pct > -min_drop_pct:
            continue

        candidates.append({
            "ticker": item.get("symbol"),
            "name": item.get("name"),
            "price_brl": q.get("value"),
            "change_pct_today": change_pct,
            "dividend_yield_12m_pct": dy,
            "market_cap": q.get("market_cap"),
        })

    candidates.sort(key=lambda x: x["dividend_yield_12m_pct"], reverse=True)
    return {
        "candidates": candidates,
        "screened": len(tickers),
        "matches": len(candidates),
    }


# ---------------------------------------------------------------------------
# Tool 4 — List strategies
# ---------------------------------------------------------------------------
@mcp.tool()
def list_strategies() -> dict:
    """List all available investment strategies with descriptions."""
    return {
        "strategies": [
            {
                "name": name,
                "buy_criterion": {
                    "rsi": "RSI < 30",
                    "ema_crossover": "EMA9 crosses above EMA21",
                    "combined": "RSI < 35 AND price above 200-day EMA",
                    "dividend_value": "5-day drop > 5% AND RSI < 40",
                }.get(name, ""),
                "sell_criterion": {
                    "rsi": "RSI > 70",
                    "ema_crossover": "EMA9 crosses below EMA21",
                    "combined": "RSI > 65",
                    "dividend_value": "RSI > 60",
                }.get(name, ""),
            }
            for name in STRATEGIES
        ],
        "universal_exits": {
            "stop_loss": "default -8% from entry",
            "take_profit": "default +20% from entry",
        },
    }


# ---------------------------------------------------------------------------
# Tool 5 — Macro context (BCB: Selic, IPCA, USD/BRL, Ibovespa)
# ---------------------------------------------------------------------------
@mcp.tool()
async def get_macro_context() -> dict:
    """
    Fetch current Brazilian macro indicators from BCB (Banco Central do Brasil).

    Returns Selic rate, IPCA 12-month, USD/BRL PTax, Ibovespa daily change,
    B3 market open/closed status, and timestamp.
    """
    ctx = await load_macro_context()
    return ctx.model_dump()


# ---------------------------------------------------------------------------
# Tool 6 — Risk analysis (VaR, Sharpe, Sortino, beta, Kelly)
# ---------------------------------------------------------------------------
@mcp.tool()
async def analyze_risk(
    ticker: str,
    period: str = "1y",
    risk_free_annual: float = 0.105,
) -> dict:
    """
    Full risk profile for a B3 stock using historical data.

    Computes:
    - VaR 95% and 99% (historical percentile method)
    - Max drawdown
    - Sharpe and Sortino ratios (annualized, vs Selic ~10.5%)
    - Beta vs IBOVESPA
    - Annualized volatility
    - Kelly Criterion position sizing (capped at 10%)

    Args:
        ticker: B3 symbol, e.g. "PETR4"
        period: History window — "6mo", "1y", "2y"
        risk_free_annual: Annual risk-free rate (default 10.5% = ~Selic)
    """
    metrics = await calculate_risk_async(ticker, period)
    return metrics.model_dump()


# ---------------------------------------------------------------------------
# Tool 7 — Circuit breaker check
# ---------------------------------------------------------------------------
@mcp.tool()
def check_stock_circuit_breaker(
    ticker: str,
    daily_loss_limit_pct: float = 2.0,
    weekly_loss_limit_pct: float = 5.0,
) -> dict:
    """
    Check if a ticker has breached daily or weekly loss thresholds.

    If triggered, all operations on this ticker should be halted.

    Args:
        ticker: B3 symbol
        daily_loss_limit_pct: Halt if daily loss >= this % (default 2%)
        weekly_loss_limit_pct: Halt if weekly loss >= this % (default 5%)
    """
    result = check_circuit_breaker(ticker, daily_loss_limit_pct, weekly_loss_limit_pct)
    return result.model_dump()


# ---------------------------------------------------------------------------
# Tool 8 — Correlation matrix
# ---------------------------------------------------------------------------
@mcp.tool()
def get_correlation_matrix(
    tickers: list[str],
    period: str = "1y",
) -> dict:
    """
    Compute pairwise Pearson correlation between B3 assets.

    Flags pairs with |correlation| >= 0.7 as high concentration risk.

    Args:
        tickers: List of B3 symbols
        period: History window — "6mo", "1y", "2y"
    """
    result = correlation_matrix(tickers, period)
    return result.model_dump()


# ---------------------------------------------------------------------------
# Tool 9 — Portfolio tracker (P&L, sector exposure)
# ---------------------------------------------------------------------------
@mcp.tool()
async def track_portfolio_positions(
    positions: list[dict],
    cash: float = 0.0,
) -> dict:
    """
    Calculate current portfolio state: market value, P&L per position,
    sector exposure, and top/worst performer.

    Args:
        positions: List of {"ticker": "PETR4", "quantity": 100, "avg_price": 35.50}
        cash: Cash balance in BRL not invested in stocks

    Returns:
        Total value, invested value, per-position P&L, sector weights,
        circuit-breaker flag (any position down > 8%).
    """
    parsed = [
        PortfolioPosition(ticker=p["ticker"].upper(), quantity=p["quantity"], avg_price=p["avg_price"])
        for p in positions
    ]
    portfolio = PortfolioInput(positions=parsed, cash=cash)
    summary = await track_portfolio(portfolio)
    return summary.model_dump()


# ---------------------------------------------------------------------------
# Tool 10 — News sentiment analysis
# ---------------------------------------------------------------------------
@mcp.tool()
async def get_sentiment(
    ticker: str,
    max_articles: int = 10,
) -> dict:
    """
    Analyze recent Portuguese-language financial news sentiment for a ticker.

    Sources: InfoMoney RSS, Investing.com BR RSS.
    Scoring: keyword lexicon (PT-BR), range -1.0 (very negative) to +1.0 (very positive).

    Args:
        ticker: B3 symbol, e.g. "PETR4"
        max_articles: Maximum headlines to return (default 10)
    """
    result = await analyze_sentiment(ticker, max_articles)
    return result.model_dump()


# ---------------------------------------------------------------------------
# Tool 11 — Technical pattern detection
# ---------------------------------------------------------------------------
@mcp.tool()
async def technical_analysis(
    ticker: str,
    period: str = "6mo",
) -> dict:
    """
    Compute technical indicators and derive a buy/sell/hold signal.

    Indicators: RSI-14, MACD (12/26/9), EMA 9/21/200,
    Bollinger Bands (20, 2σ), candlestick patterns.

    Returns signal ("buy" | "sell" | "hold"), confidence 0-1,
    and list of supporting reasons.

    Args:
        ticker: B3 symbol, e.g. "PETR4"
        period: Data window — "3mo", "6mo", "1y"
    """
    result = await detect_patterns_async(ticker, period)
    return result.model_dump()


# ---------------------------------------------------------------------------
# Tool 12 — Fundamental analysis
# ---------------------------------------------------------------------------
@mcp.tool()
async def fundamental_analysis(
    ticker: str,
) -> dict:
    """
    Fetch key fundamental metrics for a B3 stock via Yahoo Finance.

    Returns P/E, P/B, ROE, EV/EBITDA, revenue growth YoY,
    net margin, D/E ratio, dividend yield, and a simplified DCF fair value.

    Args:
        ticker: B3 symbol, e.g. "PETR4"
    """
    result = await parse_quarterly_earnings_async(ticker)
    return result.model_dump()


# ---------------------------------------------------------------------------
# Tool 13 — DCF valuation (configurable)
# ---------------------------------------------------------------------------
@mcp.tool()
def run_dcf_valuation(
    ticker: str,
    wacc: float = 0.12,
    growth_rate: float = 0.05,
) -> dict:
    """
    Run a simplified DCF valuation with configurable WACC and growth rate.

    Model: P = EPS × (1 + g) / (WACC − g)

    Args:
        ticker: B3 symbol
        wacc: Weighted average cost of capital (default 12% — Brazilian risk premium)
        growth_rate: Perpetual earnings growth rate (default 5%)
    """
    return dcf_valuation(ticker, wacc, growth_rate)


# ---------------------------------------------------------------------------
# Tool 14 — Peer comparison
# ---------------------------------------------------------------------------
@mcp.tool()
async def compare_peers(
    ticker: str,
    peers: list[str],
) -> dict:
    """
    Compare a B3 stock against sector peers on key fundamental multiples.

    Metrics: P/E, P/B, ROE, EV/EBITDA, dividend yield, net margin.

    Args:
        ticker: Main ticker to evaluate, e.g. "PETR4"
        peers: Peer tickers, e.g. ["CSAN3", "UGPA3", "VBBR3"]
    """
    result = await peer_comparison_async(ticker, peers)
    return result.model_dump()


# ---------------------------------------------------------------------------
# Tool 15 — Pipeline completo de investimentos
# ---------------------------------------------------------------------------
@mcp.tool()
async def run_investing_decision(
    watchlist: list[str],
    positions: list[dict] | None = None,
    cash: float = 0.0,
) -> dict:
    """
    Executa o pipeline completo do Playbook de Investimentos (longo prazo).

    Passos internos:
    1. Pré-análise: macro (Selic/IPCA/USD/Ibovespa), mercado aberto, modo conservador
    2. Avaliação da carteira: P&L, stops, concentração, sinais de venda
    3. Screening: score combinado técnica+fundamental+sentimento+macro para watchlist
    4. Gestão de risco: Kelly position sizing, circuit breaker, reserva de caixa
    5. Decisão: recomendações de venda (com urgência) e compra (com tamanho BRL)

    Args:
        watchlist: tickers a avaliar para compra, ex: ["PETR4", "VALE3", "ITUB4"]
        positions: posições atuais, ex: [{"ticker": "BBAS3", "quantity": 100, "avg_price": 28.50}]
        cash: saldo em caixa em BRL

    Returns:
        InvestingDecision com sell_signals, buy_recommendations e alertas
    """
    from app.models import PortfolioInput, PortfolioPosition

    portfolio = None
    if positions:
        parsed = [
            PortfolioPosition(
                ticker=p["ticker"].upper(),
                quantity=p["quantity"],
                avg_price=p["avg_price"],
            )
            for p in positions
        ]
        portfolio = PortfolioInput(positions=parsed, cash=cash)

    tickers = [t.strip().upper() for t in watchlist]
    decision = await run_investing_pipeline(tickers, portfolio)
    return decision.model_dump()


# ---------------------------------------------------------------------------
# Tool 16 — Score combinado por ticker
# ---------------------------------------------------------------------------
@mcp.tool()
async def score_tickers(tickers: list[str]) -> dict:
    """
    Score combinado de compra para múltiplos tickers B3.

    Pondera: técnica 40% + fundamentalista 40% + sentimento 10% + macro 10%.
    Score >= 0.6 → recomendação "buy". Filtros de qualidade são gates hard.

    Args:
        tickers: lista de símbolos B3, ex: ["PETR4", "VALE3", "ITUB4"]

    Returns:
        Lista ordenada por score desc com breakdown e recomendação por ticker
    """
    symbols = [t.strip().upper() for t in tickers]
    results = await score_watchlist(symbols)
    return {"results": [r.model_dump() for r in results], "count": len(results)}


# ---------------------------------------------------------------------------
# Tool 17 — Save agent decision (experiment persistence)
# ---------------------------------------------------------------------------
@mcp.tool()
def save_decision(
    session_id: str,
    decision: dict,
) -> dict:
    """
    Persist a full agent decision context to SQLite for the 5-day experiment.

    Call this at the end of every decision cycle so the log is complete.

    Args:
        session_id: Unique identifier for this agent session (e.g. "2026-05-26-10h")
        decision: Full decision dict — macro context, scores, sell signals,
                  buy recommendations, reasoning. Any JSON-serialisable structure.

    Returns:
        {"saved": true, "id": <row_id>}
    """
    row_id = _save_decision(session_id, decision)
    return {"saved": True, "id": row_id}


# ---------------------------------------------------------------------------
# Tool 18 — Get decision log (experiment read-back)
# ---------------------------------------------------------------------------
@mcp.tool()
def get_decision_log(
    date_filter: Optional[str] = None,
    last_n: Optional[int] = None,
) -> dict:
    """
    Retrieve saved agent decisions from the experiment log.

    Filters (use one at a time):
    - date_filter: ISO date string "YYYY-MM-DD" — returns all decisions for that day
    - last_n: integer — returns the N most recent decisions

    If neither is given, returns the entire log.

    Args:
        date_filter: e.g. "2026-05-26"
        last_n: e.g. 5

    Returns:
        {"decisions": [...], "count": N}
    """
    rows = _get_decision_log(date_filter, last_n)
    return {"decisions": rows, "count": len(rows)}


# ---------------------------------------------------------------------------
# Tool 19 — Save paper trade (virtual execution)
# ---------------------------------------------------------------------------
@mcp.tool()
def save_paper_trade(
    action: str,
    ticker: str,
    price: float,
    quantity: float,
    reason: Optional[str] = None,
    session_id: Optional[str] = None,
) -> dict:
    """
    Record a virtual buy or sell action for paper trading during the experiment.

    No real money moves. This is the execution log for tracking decisions.

    Args:
        action: "buy" or "sell"
        ticker: B3 symbol, e.g. "PETR4"
        price: Execution price in BRL (use current market price from get_stock_quotes)
        quantity: Number of shares (can be fractional for BRL-based sizing)
        reason: Short human-readable rationale, e.g. "RSI oversold + above EMA200"
        session_id: Optional session tag to group trades with decisions

    Returns:
        {"saved": true, "id": <row_id>, "trade_value_brl": <price * quantity>}
    """
    if action.lower() not in ("buy", "sell"):
        return {"error": f"action must be 'buy' or 'sell', got '{action}'"}
    row_id = _save_paper_trade(action, ticker, price, quantity, reason, session_id)
    return {
        "saved": True,
        "id": row_id,
        "trade_value_brl": round(price * quantity, 2),
    }


# ---------------------------------------------------------------------------
# Tool 20 — Get paper portfolio (open positions)
# ---------------------------------------------------------------------------
@mcp.tool()
def get_paper_portfolio() -> dict:
    """
    Return current open paper positions (buys not yet sold).

    Uses FIFO matching to compute open quantity and average buy price per ticker.
    Combine with get_stock_quotes to compute live unrealized P&L.

    Returns:
        {"positions": [...], "count": N}
        Each position: ticker, open_quantity, avg_buy_price, total_cost_brl, first_buy_at
    """
    positions = _get_paper_portfolio()
    return {"positions": positions, "count": len(positions)}


# ---------------------------------------------------------------------------
# Tool 21 — Get trade outcomes (realized + open P&L)
# ---------------------------------------------------------------------------
@mcp.tool()
def get_trade_outcomes(
    since_date: Optional[str] = None,
) -> dict:
    """
    Compute P&L outcomes for all paper trades since a given date.

    For completed round-trips (buy + sell): realized P&L in BRL and %.
    For open positions: returns cost basis (combine with get_stock_quotes for live P&L).

    Args:
        since_date: ISO date "YYYY-MM-DD" — filter trades from this date onward.
                    Omit to get all-time results.

    Returns:
        completed_trades, realized_pnl_brl, open_positions, period_from
    """
    return _get_trade_outcomes(since_date)


if __name__ == "__main__":
    transport = "stdio"
    port = 8001
    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--transport" and i + 2 <= len(sys.argv) - 1:
            transport = sys.argv[i + 2]
        if arg == "--port" and i + 2 <= len(sys.argv) - 1:
            port = int(sys.argv[i + 2])

    if transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http")
