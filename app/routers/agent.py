"""
/agent — endpoints de orquestração do pipeline de investimentos.
"""
from fastapi import APIRouter
from pydantic import BaseModel

from app.agent.investing_pipeline import run_investing_pipeline
from app.models import PortfolioInput, PortfolioPosition

router = APIRouter(prefix="/agent", tags=["agent"])


class PipelineRequest(BaseModel):
    watchlist: list[str]
    positions: list[dict] = []
    cash: float = 0.0


@router.post("/investing")
async def investing_pipeline(body: PipelineRequest):
    """
    Executa o pipeline completo de investimentos.

    - Pré-análise: mercado, macro, modo conservador
    - Avaliação da carteira: P&L, stops, concentração, sinais de venda
    - Screening: score técnica+fundamentalista+sentimento+macro para cada ticker da watchlist
    - Gestão de risco: Kelly position sizing, circuit breaker, reserva de caixa
    - Decisão: recomendações de venda e compra com tamanhos

    Body:
    ```json
    {
      "watchlist": ["PETR4", "VALE3", "ITUB4"],
      "positions": [{"ticker": "BBAS3", "quantity": 100, "avg_price": 28.50}],
      "cash": 5000.0
    }
    ```
    """
    portfolio = None
    if body.positions:
        parsed = [
            PortfolioPosition(
                ticker=p["ticker"].upper(),
                quantity=p["quantity"],
                avg_price=p["avg_price"],
            )
            for p in body.positions
        ]
        portfolio = PortfolioInput(positions=parsed, cash=body.cash)

    watchlist = [t.strip().upper() for t in body.watchlist]
    decision = await run_investing_pipeline(watchlist, portfolio)
    return decision.model_dump()


class ScorerRequest(BaseModel):
    tickers: list[str]


@router.post("/score")
async def score_tickers(body: ScorerRequest):
    """
    Score combinado (técnica 40% + fundamental 40% + sentimento 10% + macro 10%)
    para uma lista de tickers. Ordena por score desc.
    """
    from app.skills.shared.scorer import score_watchlist
    tickers = [t.strip().upper() for t in body.tickers]
    results = await score_watchlist(tickers)
    return {"results": [r.model_dump() for r in results], "count": len(results)}
