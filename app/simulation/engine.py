"""
Backtesting engine.

Uses yfinance for historical OHLCV data.
B3 tickers require the .SA suffix (added automatically if missing).
US tickers pass through unchanged.
"""
import asyncio
from typing import Optional

import pandas as pd
import yfinance as yf

from app.models import Position, SimulationResult, Trade
from app.simulation.strategies import STRATEGIES, combined_strategy


def _to_yf_ticker(ticker: str) -> str:
    """PETR4 → PETR4.SA  |  AAPL → AAPL  |  PETR4.SA → PETR4.SA"""
    ticker = ticker.strip().upper()
    if "." in ticker:
        return ticker
    # Heuristic: tickers ending in a digit are B3
    if ticker[-1].isdigit():
        return f"{ticker}.SA"
    return ticker


def _fetch_ohlcv(ticker: str, start: str, end: str) -> pd.DataFrame:
    yf_sym = _to_yf_ticker(ticker)
    df = yf.download(yf_sym, start=start, end=end, auto_adjust=True, progress=False)
    if df.empty:
        raise ValueError(f"No price data for '{ticker}' ({yf_sym}) in range {start}→{end}")
    # Flatten MultiIndex columns (yfinance >= 0.2.40 wraps single ticker in MultiIndex)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    df = df.dropna(subset=["Close"])
    return df


def _max_drawdown(equity: list[float]) -> float:
    peak = equity[0]
    max_dd = 0.0
    for v in equity:
        if v > peak:
            peak = v
        dd = (peak - v) / peak * 100 if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
    return max_dd


def run_simulation(
    ticker: str,
    start_date: str,
    end_date: str,
    initial_capital: float = 10_000.0,
    strategy: str = "combined",
    stop_loss_pct: float = 0.08,
    take_profit_pct: float = 0.20,
) -> SimulationResult:
    df = _fetch_ohlcv(ticker, start_date, end_date)
    strategy_fn = STRATEGIES.get(strategy, combined_strategy)
    signals = strategy_fn(df)

    capital = initial_capital
    shares = 0.0
    entry_price = 0.0
    trades: list[Trade] = []
    equity_curve: list[float] = []

    for date in df.index:
        price = float(df.loc[date, "Close"])
        sig = int(signals.loc[date]) if not pd.isna(signals.loc[date]) else 0
        date_str = date.strftime("%Y-%m-%d")

        # --- Stop-loss / take-profit exit ---
        if shares > 0:
            pnl_pct = (price - entry_price) / entry_price
            exit_reason: Optional[str] = None
            if pnl_pct <= -stop_loss_pct:
                exit_reason = f"stop-loss ({pnl_pct:.1%})"
            elif pnl_pct >= take_profit_pct:
                exit_reason = f"take-profit ({pnl_pct:.1%})"
            if exit_reason:
                capital += shares * price
                trades.append(Trade(
                    ticker=ticker, action="sell",
                    quantity=round(shares, 4), price=price,
                    date=date_str, reason=exit_reason,
                ))
                shares = 0.0
                equity_curve.append(capital)
                continue

        # --- Strategy signal ---
        if sig == 1 and shares == 0 and capital >= price:
            shares = capital / price
            capital = 0.0
            entry_price = price
            trades.append(Trade(
                ticker=ticker, action="buy",
                quantity=round(shares, 4), price=price,
                date=date_str, reason=strategy,
            ))
        elif sig == -1 and shares > 0:
            capital += shares * price
            trades.append(Trade(
                ticker=ticker, action="sell",
                quantity=round(shares, 4), price=price,
                date=date_str, reason=strategy,
            ))
            shares = 0.0

        equity_curve.append(capital + shares * price)

    # Liquidate open position at simulation end
    final_price = float(df["Close"].iloc[-1])
    final_portfolio: list[Position] = []
    if shares > 0:
        position_value = shares * final_price
        unrealized_pnl = (final_price - entry_price) / entry_price * 100
        final_portfolio.append(Position(
            ticker=ticker,
            quantity=round(shares, 4),
            avg_price=round(entry_price, 2),
            entry_date=next(
                (t.date for t in reversed(trades) if t.action == "buy"), start_date
            ),
            current_value=round(position_value, 2),
            unrealized_pnl_pct=round(unrealized_pnl, 2),
        ))
        capital += position_value

    # Win/loss stats (matched pairs)
    sell_trades = [t for t in trades if t.action == "sell"]
    buy_trades = [t for t in trades if t.action == "buy"]
    winning = 0
    losing = 0
    for i, sell in enumerate(sell_trades):
        if i < len(buy_trades):
            pnl = sell.price - buy_trades[i].price
            if pnl > 0:
                winning += 1
            else:
                losing += 1

    total_round_trips = winning + losing
    win_rate = (winning / total_round_trips * 100) if total_round_trips > 0 else 0.0
    total_return = (capital - initial_capital) / initial_capital * 100

    return SimulationResult(
        ticker=ticker,
        strategy=strategy,
        period_start=df.index[0].strftime("%Y-%m-%d"),
        period_end=df.index[-1].strftime("%Y-%m-%d"),
        initial_capital=initial_capital,
        final_capital=round(capital, 2),
        total_return_percent=round(total_return, 2),
        max_drawdown_percent=round(_max_drawdown(equity_curve), 2) if equity_curve else 0.0,
        total_trades=len(trades),
        winning_trades=winning,
        losing_trades=losing,
        win_rate_percent=round(win_rate, 2),
        trades=trades,
        final_portfolio=final_portfolio,
    )


async def run_simulation_async(*args, **kwargs) -> SimulationResult:
    """Run blocking simulation in thread pool so FastAPI stays non-blocking."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: run_simulation(*args, **kwargs))
