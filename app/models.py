from typing import Optional, Any
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


# --- Macro ---

class MacroContext(BaseModel):
    market_open: bool
    selic_rate: Optional[float] = None
    usd_brl: Optional[float] = None
    ipca_12m: Optional[float] = None
    ibovespa_change_pct: Optional[float] = None
    timestamp: str


# --- Risk ---

class RiskMetrics(BaseModel):
    ticker: str
    period: str
    var_95: float
    var_99: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    beta: float
    volatility_annual_pct: float
    kelly_fraction: float
    kelly_position_pct: float


class CircuitBreakerResult(BaseModel):
    ticker: str
    triggered: bool
    reason: str
    daily_return_pct: Optional[float] = None
    weekly_return_pct: Optional[float] = None


class CorrelationResult(BaseModel):
    tickers: list[str]
    matrix: dict[str, Any]
    high_correlation_pairs: list[dict[str, Any]]


# --- Sentiment ---

class NewsItem(BaseModel):
    title: str
    source: str
    pub_date: str
    sentiment_score: float


class SentimentResult(BaseModel):
    ticker: str
    score: float
    label: str  # "positive" | "neutral" | "negative"
    articles_analyzed: int
    relevant_headlines: list[NewsItem]
    timestamp: str


# --- Portfolio ---

class PortfolioPosition(BaseModel):
    ticker: str
    quantity: float
    avg_price: float


class PortfolioInput(BaseModel):
    positions: list[PortfolioPosition]
    cash: float = 0.0


class PositionDetail(BaseModel):
    ticker: str
    quantity: float
    avg_price: float
    current_price: float
    current_value: float
    pnl_brl: float
    pnl_pct: float
    sector: str
    weight_pct: float


class PortfolioSummary(BaseModel):
    total_value: float
    cash: float
    invested_value: float
    positions: list[PositionDetail]
    sector_exposure: dict[str, float]
    total_pnl_pct: float
    top_performer: Optional[str] = None
    worst_performer: Optional[str] = None
    circuit_breaker_triggered: bool


# --- Technical Analysis ---

class TechnicalSignal(BaseModel):
    ticker: str
    timestamp: str
    rsi_14: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    ema_9: Optional[float] = None
    ema_21: Optional[float] = None
    ema_200: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_mid: Optional[float] = None
    bb_lower: Optional[float] = None
    candlestick_pattern: Optional[str] = None
    signal: str  # "buy" | "sell" | "hold"
    confidence: float  # 0.0-1.0
    reasons: list[str]


# --- Fundamental Analysis ---

class FundamentalMetrics(BaseModel):
    ticker: str
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    roe: Optional[float] = None
    ev_ebitda: Optional[float] = None
    revenue_growth_yoy: Optional[float] = None
    net_margin: Optional[float] = None
    debt_equity: Optional[float] = None
    dividend_yield: Optional[float] = None
    dcf_fair_value: Optional[float] = None
    current_price: Optional[float] = None
    upside_pct: Optional[float] = None


class PeerComparison(BaseModel):
    ticker: str
    peers: list[str]
    metrics: dict[str, Any]  # {ticker: {metric: value}}
