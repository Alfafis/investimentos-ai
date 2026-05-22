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

from app.hgbrasil.client import get_quotes
from app.simulation.engine import run_simulation
from app.simulation.strategies import STRATEGIES

mcp = FastMCP(
    "investimentos-ai",
    instructions=(
        "Financial AI tools for the Brazilian stock market (B3). "
        "Use get_stock_quotes for real-time prices, simulate_investment for backtesting, "
        "and screen_stocks to filter buy candidates."
    ),
)


# ---------------------------------------------------------------------------
# Tool 1 — Real-time quotes (HG Brasil)
# ---------------------------------------------------------------------------
@mcp.tool()
async def get_stock_quotes(
    tickers: list[str],
    sort: Optional[str] = None,
) -> dict:
    """
    Fetch current B3 stock quotes from HG Brasil API.

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
        mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
