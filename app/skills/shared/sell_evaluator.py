"""
sell_evaluator — avalia critérios de venda para cada posição da carteira.

Gatilhos (em ordem de prioridade):
1. Stop-loss ≤ -8%          → venda imediata (100%)
2. Take-profit ≥ +20%       → venda parcial ou total (planejada)
3. Concentração > 10%       → redução proporcional (planejada)
4. Reversão técnica         → RSI > 70 + MACD bearish (planejada)
5. Deterioração fundamental → ROE < 5% ou P/L > 30 (planejada)
"""
from app.models import FundamentalMetrics, PositionDetail, SellSignal, TechnicalSignal

_STOP_LOSS_PCT = -8.0
_TAKE_PROFIT_PCT = 20.0
_MAX_POSITION_WEIGHT_PCT = 10.0
_FUNDAMENTAL_ROE_FLOOR = 5.0
_FUNDAMENTAL_PE_CEILING = 30.0


def evaluate_sell(
    position: PositionDetail,
    technical: TechnicalSignal | None = None,
    fundamental: FundamentalMetrics | None = None,
) -> SellSignal:
    """
    Avalia critérios de venda para uma posição.

    Args:
        position: PositionDetail com pnl_pct e weight_pct atuais
        technical: TechnicalSignal atual (opcional — se ausente, skip técnico)
        fundamental: FundamentalMetrics atual (opcional — se ausente, skip fundamental)

    Returns:
        SellSignal com action, urgency, % sugerida de venda e razões
    """
    reasons: list[str] = []
    action = "hold"
    urgency = "none"
    suggested_sell_pct = 0.0

    # 1. Stop-loss — máxima prioridade
    if position.pnl_pct <= _STOP_LOSS_PCT:
        action = "sell"
        urgency = "immediate"
        suggested_sell_pct = 100.0
        reasons.append(
            f"Stop-loss atingido: P&L {position.pnl_pct:.2f}% ≤ -{abs(_STOP_LOSS_PCT):.0f}%"
        )
        return SellSignal(
            ticker=position.ticker,
            action=action,
            urgency=urgency,
            suggested_sell_pct=suggested_sell_pct,
            reasons=reasons,
        )

    # 2. Take-profit
    if position.pnl_pct >= _TAKE_PROFIT_PCT:
        action = "sell"
        urgency = "planned"
        suggested_sell_pct = 50.0  # venda parcial — mantém exposição residual
        reasons.append(
            f"Take-profit atingido: P&L {position.pnl_pct:.2f}% ≥ +{_TAKE_PROFIT_PCT:.0f}%"
        )

    # 3. Concentração excessiva
    if position.weight_pct > _MAX_POSITION_WEIGHT_PCT:
        excess = position.weight_pct - _MAX_POSITION_WEIGHT_PCT
        reduce_pct = round(excess / position.weight_pct * 100, 1)
        if action == "hold":
            action = "reduce"
            urgency = "planned"
        suggested_sell_pct = max(suggested_sell_pct, reduce_pct)
        reasons.append(
            f"Concentração {position.weight_pct:.1f}% > limite {_MAX_POSITION_WEIGHT_PCT:.0f}%"
            f" — reduzir {reduce_pct:.1f}% da posição"
        )

    # 4. Reversão técnica (RSI overbought + MACD bearish)
    if technical is not None:
        rsi = technical.rsi_14
        macd_hist = technical.macd_hist
        if rsi is not None and macd_hist is not None:
            if rsi > 70 and macd_hist < 0:
                if action == "hold":
                    action = "reduce"
                    urgency = "planned"
                    suggested_sell_pct = max(suggested_sell_pct, 30.0)
                reasons.append(
                    f"Reversão técnica: RSI {rsi:.1f} (overbought) + MACD histograma negativo"
                )
        elif rsi is not None and rsi > 75:
            if action == "hold":
                action = "reduce"
                urgency = "planned"
                suggested_sell_pct = max(suggested_sell_pct, 20.0)
            reasons.append(f"RSI extremo: {rsi:.1f} > 75")

    # 5. Deterioração fundamental
    if fundamental is not None:
        if fundamental.roe is not None and fundamental.roe < _FUNDAMENTAL_ROE_FLOOR:
            if action == "hold":
                action = "reduce"
                urgency = "planned"
                suggested_sell_pct = max(suggested_sell_pct, 50.0)
            reasons.append(
                f"ROE deteriorado: {fundamental.roe:.1f}% < {_FUNDAMENTAL_ROE_FLOOR:.0f}%"
            )
        if fundamental.pe_ratio is not None and fundamental.pe_ratio > _FUNDAMENTAL_PE_CEILING:
            if action == "hold":
                action = "reduce"
                urgency = "planned"
                suggested_sell_pct = max(suggested_sell_pct, 25.0)
            reasons.append(
                f"P/L elevado: {fundamental.pe_ratio:.1f}x > {_FUNDAMENTAL_PE_CEILING:.0f}x"
            )

    return SellSignal(
        ticker=position.ticker,
        action=action,
        urgency=urgency,
        suggested_sell_pct=suggested_sell_pct,
        reasons=reasons,
    )
