"""
investing_pipeline — orquestrador do Playbook de Investimentos (longo prazo).

Pipeline completo:
  Pré-Análise → Avaliação da Carteira → Screening → Gestão de Risco → Decisão

Executa todas as skills em paralelo onde possível.
Retorna InvestingDecision com sinais de venda, recomendações de compra e alertas.
"""
import asyncio
from datetime import datetime, timezone

from app.models import (
    BuyRecommendation,
    InvestingDecision,
    PortfolioInput,
    PortfolioSummary,
    ScoreBreakdown,
    SellSignal,
)
from app.skills.shared.macro import load_macro_context
from app.skills.shared.portfolio import track_portfolio
from app.skills.shared.risk import calculate_risk_async, check_circuit_breaker
from app.skills.shared.scorer import score_watchlist
from app.skills.shared.sell_evaluator import evaluate_sell
from app.skills.stocks.fundamental import parse_quarterly_earnings_async
from app.skills.stocks.technical import detect_patterns_async

_CONSERVATIVE_MODE_IBOV_PCT = -3.0
_MAX_POSITION_WEIGHT_PCT = 10.0
_MIN_CASH_RESERVE_PCT = 10.0
_MAX_POSITIONS = 10
_MAX_SINGLE_ALLOCATION_PCT = 10.0
_RISK_PER_TRADE_PCT = 2.0


def _kelly_allocation(kelly_fraction: float, total_capital: float) -> float:
    """Kelly capped at _MAX_SINGLE_ALLOCATION_PCT% do capital total."""
    pct = min(kelly_fraction * 100, _MAX_SINGLE_ALLOCATION_PCT)
    return round(pct, 2), round(total_capital * pct / 100, 2)


async def _evaluate_position(position, macro):
    """Fetches technical + fundamental para uma posição e avalia sinal de venda."""
    ticker = position.ticker
    try:
        technical, fundamental = await asyncio.gather(
            detect_patterns_async(ticker),
            parse_quarterly_earnings_async(ticker),
            return_exceptions=True,
        )
        tech = technical if not isinstance(technical, Exception) else None
        fund = fundamental if not isinstance(fundamental, Exception) else None
    except Exception:
        tech, fund = None, None

    return evaluate_sell(position, technical=tech, fundamental=fund)


async def run_investing_pipeline(
    watchlist: list[str],
    portfolio: PortfolioInput | None = None,
) -> InvestingDecision:
    """
    Executa o pipeline completo de investimentos.

    Args:
        watchlist: tickers a avaliar para compra, ex: ["PETR4", "VALE3", "ITUB4"]
        portfolio: posições e caixa atuais (opcional — sem carteira, pula avaliação de venda)

    Returns:
        InvestingDecision com sinais de venda, recomendações de compra e alertas
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    alerts: list[str] = []

    # ── Step 1: Pré-Análise — macro + portfolio em paralelo ──────────────────
    macro, portfolio_summary = await asyncio.gather(
        load_macro_context(),
        track_portfolio(portfolio) if portfolio else _noop(None),
    )

    market_open = macro.market_open
    ibov = macro.ibovespa_change_pct or 0.0
    conservative_mode = ibov <= _CONSERVATIVE_MODE_IBOV_PCT

    if not market_open:
        alerts.append("Mercado fechado — análise gerada para próxima abertura")
    if conservative_mode:
        alerts.append(
            f"Modo conservador ativo: Ibovespa {ibov:+.2f}% — novas compras suspensas"
        )

    # ── Step 2: Avaliação da Carteira ─────────────────────────────────────────
    sell_signals: list[SellSignal] = []
    circuit_breaker_triggered = False

    if portfolio_summary is not None:
        circuit_breaker_triggered = portfolio_summary.circuit_breaker_triggered
        if circuit_breaker_triggered:
            alerts.append("CIRCUIT BREAKER: posição com queda > 8% — operações suspensas")

        # Verifica concentração e alertas de carteira
        cash_pct = (portfolio_summary.cash / portfolio_summary.total_value * 100
                    if portfolio_summary.total_value > 0 else 100.0)
        if cash_pct < _MIN_CASH_RESERVE_PCT:
            alerts.append(
                f"Reserva de caixa {cash_pct:.1f}% abaixo do mínimo {_MIN_CASH_RESERVE_PCT:.0f}%"
            )

        active_positions = len(portfolio_summary.positions)
        if active_positions >= _MAX_POSITIONS:
            alerts.append(
                f"Máximo de posições atingido ({active_positions}/{_MAX_POSITIONS})"
            )

        # Avalia sinais de venda para cada posição em paralelo
        sell_tasks = [
            _evaluate_position(pos, macro)
            for pos in portfolio_summary.positions
        ]
        sell_results = await asyncio.gather(*sell_tasks, return_exceptions=True)
        sell_signals = [r for r in sell_results if isinstance(r, SellSignal)]

        immediate_sells = [s for s in sell_signals if s.urgency == "immediate"]
        if immediate_sells:
            tickers = ", ".join(s.ticker for s in immediate_sells)
            alerts.append(f"VENDA IMEDIATA recomendada: {tickers}")

    # ── Step 3: Screening de Oportunidades ───────────────────────────────────
    buy_recommendations: list[BuyRecommendation] = []

    # Não faz novas compras se: circuit breaker, modo conservador ou max posições
    can_buy = (
        not circuit_breaker_triggered
        and not conservative_mode
        and (portfolio_summary is None or len(portfolio_summary.positions) < _MAX_POSITIONS)
    )

    if can_buy and watchlist:
        scored = await score_watchlist(watchlist, macro_context=macro)
        buy_candidates = [s for s in scored if s.recommendation == "buy"]

        total_capital = portfolio_summary.total_value if portfolio_summary else 0.0
        available_cash = portfolio_summary.cash if portfolio_summary else 0.0

        for candidate in buy_candidates:
            # Kelly-based position sizing via risk metrics
            try:
                risk = await calculate_risk_async(candidate.ticker)
                kelly = risk.kelly_fraction
            except Exception:
                kelly = 0.02  # fallback conservador: 2%

            alloc_pct, alloc_brl = _kelly_allocation(kelly, total_capital)

            # Limita ao caixa disponível
            alloc_brl = min(alloc_brl, available_cash * 0.95)

            if alloc_brl < 100:
                continue  # muito pequeno para operar

            buy_recommendations.append(BuyRecommendation(
                ticker=candidate.ticker,
                score=candidate.score.combined,
                score_breakdown=candidate.score,
                recommended_capital_pct=alloc_pct,
                recommended_brl=round(alloc_brl, 2),
                reasons=candidate.reasons,
            ))

        if not buy_candidates and watchlist:
            alerts.append(
                f"Nenhum ticker da watchlist atingiu score >= 0.6 para compra "
                f"(melhor: {scored[0].ticker} = {scored[0].score.combined:.3f})"
                if scored else "Watchlist vazia ou erro no scoring"
            )

    return InvestingDecision(
        timestamp=timestamp,
        market_open=market_open,
        conservative_mode=conservative_mode,
        macro=macro,
        portfolio=portfolio_summary,
        sell_signals=sell_signals,
        buy_recommendations=buy_recommendations,
        alerts=alerts,
        circuit_breaker_triggered=circuit_breaker_triggered,
    )


async def _noop(val):
    return val
