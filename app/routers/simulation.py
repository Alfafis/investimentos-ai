from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.models import SimulationResult
from app.simulation.engine import run_simulation_async
from app.simulation.strategies import STRATEGIES

router = APIRouter(prefix="/simulation", tags=["simulation"])

_VALID_STRATEGIES = list(STRATEGIES.keys())


class SimulationRequest(BaseModel):
    ticker: str = Field(..., description="B3 ticker, e.g. PETR4 or VALE3")
    start_date: str = Field(..., description="YYYY-MM-DD")
    end_date: str = Field(..., description="YYYY-MM-DD")
    initial_capital: float = Field(10_000.0, gt=0, description="Initial capital in BRL")
    strategy: str = Field(
        "combined",
        description=f"Strategy name. Options: {', '.join(_VALID_STRATEGIES)}",
    )
    stop_loss_pct: float = Field(0.08, gt=0, lt=1, description="Stop-loss threshold, e.g. 0.08 = 8%")
    take_profit_pct: float = Field(0.20, gt=0, description="Take-profit threshold, e.g. 0.20 = 20%")


@router.post(
    "/",
    response_model=SimulationResult,
    summary="Backtest a strategy on historical data",
)
async def simulate(req: SimulationRequest):
    if req.strategy not in STRATEGIES:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown strategy '{req.strategy}'. Valid: {_VALID_STRATEGIES}",
        )
    try:
        result = await run_simulation_async(
            ticker=req.ticker,
            start_date=req.start_date,
            end_date=req.end_date,
            initial_capital=req.initial_capital,
            strategy=req.strategy,
            stop_loss_pct=req.stop_loss_pct,
            take_profit_pct=req.take_profit_pct,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Simulation error: {exc}") from exc
    return result


@router.get(
    "/strategies",
    summary="List available strategies",
)
async def list_strategies():
    return {
        "strategies": [
            {
                "name": "rsi",
                "description": "Pure RSI — buy RSI < 30, sell RSI > 70",
            },
            {
                "name": "ema_crossover",
                "description": "EMA 9/21 crossover — buy on bullish cross, sell on bearish",
            },
            {
                "name": "combined",
                "description": "RSI + 200 EMA trend filter — buy RSI < 35 above EMA200, sell RSI > 65 (recommended)",
            },
            {
                "name": "dividend_value",
                "description": "Dip buyer — buy on 5-day -5% drop with RSI < 40, sell RSI > 60",
            },
        ]
    }
