from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.quotes.client import get_quotes as _get_quotes
from app.models import Classification, Dividends, Quote, QuotesResponse, StockResult

router = APIRouter(prefix="/quotes", tags=["quotes"])


def _parse_results(data: dict) -> list[StockResult]:
    results = []
    for item in data.get("results", []):
        q = item.get("quote") or {}
        div = item.get("dividends") or {}
        cls = item.get("classification") or {}
        results.append(StockResult(
            ticker=item.get("ticker", ""),
            kind=item.get("kind", "stock"),
            currency=item.get("currency", "BRL"),
            symbol=item.get("symbol", ""),
            name=item.get("name", ""),
            full_name=item.get("full_name"),
            classification=Classification(**cls) if cls else None,
            quote=Quote(
                value=q.get("value", 0.0),
                change_value=q.get("change_value", 0.0),
                change_percent=q.get("change_percent", 0.0),
                market_cap=q.get("market_cap"),
                updated_at=q.get("updated_at", ""),
            ),
            dividends=Dividends(
                yield_12m_percent=div.get("yield_12m_percent"),
                yield_12m_cash=div.get("yield_12m_cash"),
            ) if div else None,
        ))
    return results


@router.get(
    "/",
    response_model=QuotesResponse,
    summary="Get current B3 stock quotes",
)
async def get_quotes(
    tickers: str = Query(..., description="Comma-separated B3 tickers, e.g. PETR4,VALE3,ITUB4"),
    sort: Optional[str] = Query(
        None,
        description="Sort field: value:asc, value:desc, change_percent:asc, change_percent:desc, volume:asc, volume:desc",
    ),
):
    b3_tickers = [f"B3:{t.strip().upper()}" for t in tickers.split(",") if t.strip()]
    if not b3_tickers:
        raise HTTPException(status_code=422, detail="At least one ticker required")
    try:
        data = await _get_quotes(b3_tickers, sort)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"quotes client error: {exc}") from exc

    meta = data.get("metadata") or {}
    return QuotesResponse(
        cached=meta.get("cached", False),
        response_time_ms=meta.get("response_time_ms", 0.0),
        results=_parse_results(data),
    )


@router.get(
    "/{ticker}",
    response_model=StockResult,
    summary="Get quote for a single ticker",
)
async def get_quote(ticker: str):
    b3_ticker = f"B3:{ticker.strip().upper()}"
    try:
        data = await _get_quotes([b3_ticker])
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"quotes client error: {exc}") from exc

    results = _parse_results(data)
    if not results:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found")
    return results[0]
