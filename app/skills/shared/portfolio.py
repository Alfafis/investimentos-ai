"""
portfolio_tracker — in-memory portfolio state with P&L and sector exposure.

No DB required for Phase 1. Portfolio state is passed in by the caller.
Phase 2: persist to PostgreSQL.
"""
from typing import Optional

import asyncio
from app.quotes.client import get_quotes
from app.models import PortfolioInput, PortfolioSummary, PositionDetail


# B3 sector mapping (simplified — covers IBOVESPA top components)
_SECTOR_MAP: dict[str, str] = {
    "PETR4": "Energia", "PETR3": "Energia",
    "VALE3": "Mineração",
    "ITUB4": "Financeiro", "ITUB3": "Financeiro",
    "BBDC4": "Financeiro", "BBDC3": "Financeiro",
    "BBAS3": "Financeiro",
    "ABEV3": "Consumo",
    "WEGE3": "Industrial",
    "RENT3": "Serviços",
    "RAIL3": "Logística",
    "SUZB3": "Papel e Celulose",
    "LREN3": "Varejo",
    "MGLU3": "Varejo",
    "RDOR3": "Saúde",
    "HAPV3": "Saúde",
    "GGBR4": "Siderurgia",
    "CSNA3": "Siderurgia",
    "UGPA3": "Energia",
    "VIVT3": "Telecom",
    "CMIG4": "Energia",
    "ELET3": "Energia", "ELET6": "Energia",
    "CPLE6": "Energia",
    "TAEE11": "Energia",
}


async def track_portfolio(portfolio: PortfolioInput) -> PortfolioSummary:
    """
    Calculate current portfolio state: market value, P&L, sector exposure.

    Args:
        portfolio: PortfolioInput with list of positions and cash balance
    """
    if not portfolio.positions:
        return PortfolioSummary(
            total_value=portfolio.cash,
            cash=portfolio.cash,
            invested_value=0.0,
            positions=[],
            sector_exposure={},
            total_pnl_pct=0.0,
            top_performer=None,
            worst_performer=None,
            circuit_breaker_triggered=False,
        )

    # Fetch current prices
    tickers = [f"B3:{p.ticker}" for p in portfolio.positions]
    try:
        data = await get_quotes(tickers)
        price_map: dict[str, float] = {}
        for item in data.get("results", []):
            sym = item.get("symbol", "")
            price_map[sym] = item.get("quote", {}).get("value", 0.0)
    except Exception:
        price_map = {}

    position_details: list[PositionDetail] = []
    sector_value: dict[str, float] = {}

    for pos in portfolio.positions:
        current_price = price_map.get(pos.ticker, pos.avg_price)
        current_value = pos.quantity * current_price
        cost_basis = pos.quantity * pos.avg_price
        pnl = current_value - cost_basis
        pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0.0
        sector = _SECTOR_MAP.get(pos.ticker, "Outros")

        position_details.append(PositionDetail(
            ticker=pos.ticker,
            quantity=pos.quantity,
            avg_price=pos.avg_price,
            current_price=round(current_price, 2),
            current_value=round(current_value, 2),
            pnl_brl=round(pnl, 2),
            pnl_pct=round(pnl_pct, 2),
            sector=sector,
            weight_pct=0.0,  # calculated below
        ))
        sector_value[sector] = sector_value.get(sector, 0.0) + current_value

    invested_value = sum(p.current_value for p in position_details)
    total_value = invested_value + portfolio.cash

    # Calculate weights
    for p in position_details:
        p.weight_pct = round(p.current_value / total_value * 100, 2) if total_value > 0 else 0.0

    # Sector exposure as % of total portfolio
    sector_exposure = {
        s: round(v / total_value * 100, 2) for s, v in sector_value.items()
    } if total_value > 0 else {}

    # Total P&L
    total_cost = sum(p.quantity * p.avg_price for p in portfolio.positions)
    total_pnl_pct = round((invested_value - total_cost) / total_cost * 100, 2) if total_cost > 0 else 0.0

    sorted_positions = sorted(position_details, key=lambda x: x.pnl_pct, reverse=True)

    # Simple circuit breaker: any position down > 8% in portfolio
    circuit_triggered = any(p.pnl_pct <= -8.0 for p in position_details)

    return PortfolioSummary(
        total_value=round(total_value, 2),
        cash=portfolio.cash,
        invested_value=round(invested_value, 2),
        positions=position_details,
        sector_exposure=sector_exposure,
        total_pnl_pct=total_pnl_pct,
        top_performer=sorted_positions[0].ticker if sorted_positions else None,
        worst_performer=sorted_positions[-1].ticker if sorted_positions else None,
        circuit_breaker_triggered=circuit_triggered,
    )
