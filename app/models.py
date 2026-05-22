from typing import Optional
from pydantic import BaseModel


class Classification(BaseModel):
    sector: Optional[str] = None
    subsector: Optional[str] = None
    segment: Optional[str] = None


class Quote(BaseModel):
    value: float
    change_value: float
    change_percent: float
    market_cap: Optional[float] = None
    updated_at: str


class Dividends(BaseModel):
    yield_12m_percent: Optional[float] = None
    yield_12m_cash: Optional[float] = None


class StockResult(BaseModel):
    ticker: str
    kind: str
    currency: str
    symbol: str
    name: str
    full_name: Optional[str] = None
    classification: Optional[Classification] = None
    quote: Quote
    dividends: Optional[Dividends] = None


class QuotesResponse(BaseModel):
    cached: bool
    response_time_ms: float
    results: list[StockResult]


class Position(BaseModel):
    ticker: str
    quantity: float
    avg_price: float
    entry_date: str
    current_value: Optional[float] = None
    unrealized_pnl_pct: Optional[float] = None


class Trade(BaseModel):
    ticker: str
    action: str  # "buy" | "sell"
    quantity: float
    price: float
    date: str
    reason: str


class SimulationResult(BaseModel):
    ticker: str
    strategy: str
    period_start: str
    period_end: str
    initial_capital: float
    final_capital: float
    total_return_percent: float
    max_drawdown_percent: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_percent: float
    trades: list[Trade]
    final_portfolio: list[Position]
