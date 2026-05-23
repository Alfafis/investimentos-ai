"""
investment_scorer — combina análise técnica, fundamentalista, sentimento e macro
em um score único 0-1 para decisão de compra.

Pesos: técnica 40% + fundamental 40% + sentimento 10% + macro 10%
Score >= 0.6 → recomendação de compra.
Filtros de qualidade são gates hard: falha = "skip" independente do score.
"""
import asyncio
from datetime import datetime, timezone

from app.models import (
    FundamentalMetrics,
    MacroContext,
    ScoreBreakdown,
    ScoreResult,
    SentimentResult,
    TechnicalSignal,
)
from app.skills.shared.macro import load_macro_context
from app.skills.shared.sentiment import analyze_sentiment
from app.skills.stocks.fundamental import parse_quarterly_earnings_async
from app.skills.stocks.technical import detect_patterns_async

_MIN_DAILY_VOLUME_BRL = 5_000_000    # R$ 5M
_MIN_MARKET_CAP_BRL = 500_000_000   # R$ 500M
_BUY_THRESHOLD = 0.60
_HOLD_THRESHOLD = 0.40


def _technical_score(signal: TechnicalSignal) -> tuple[float, list[str]]:
    reasons = []
    if signal.signal == "buy":
        score = signal.confidence
        reasons.append(f"Técnica: sinal de compra (confiança {signal.confidence:.0%})")
    elif signal.signal == "sell":
        score = 1.0 - signal.confidence
        reasons.append(f"Técnica: sinal de venda (confiança {signal.confidence:.0%})")
    else:
        score = 0.5
        reasons.append("Técnica: neutro")
    return round(score, 3), reasons


def _fundamental_score(fm: FundamentalMetrics) -> tuple[float, list[str]]:
    points = 0
    total = 0
    reasons = []

    checks = [
        (fm.pe_ratio is not None and fm.pe_ratio < 20,    "P/L < 20"),
        (fm.roe is not None and fm.roe > 10,              "ROE > 10%"),
        (fm.debt_equity is not None and fm.debt_equity < 3.0, "Dívida/PL < 3x"),
        (fm.dividend_yield is not None and fm.dividend_yield > 0, "Dividend yield > 0"),
        (fm.upside_pct is not None and fm.upside_pct > 10, "DCF upside > 10%"),
    ]

    for passed, label in checks:
        total += 1
        if passed:
            points += 1
            reasons.append(f"Fundamental: {label}")

    score = round(points / total, 3) if total > 0 else 0.5
    return score, reasons


def _sentiment_score(sr: SentimentResult) -> tuple[float, list[str]]:
    # sr.score: -1 to +1 → normalize to 0-1
    score = round((sr.score + 1) / 2, 3)
    reasons = [f"Sentimento: {sr.label} (score {sr.score:+.3f}, {sr.articles_analyzed} artigos)"]
    return score, reasons


def _macro_score(ctx: MacroContext) -> tuple[float, list[str]]:
    reasons = []
    ibov = ctx.ibovespa_change_pct or 0.0

    if ibov >= 1.0:
        score = 0.75
        reasons.append(f"Macro: Ibovespa em alta ({ibov:+.2f}%)")
    elif ibov <= -3.0:
        score = 0.10
        reasons.append(f"Macro: Ibovespa em forte queda ({ibov:+.2f}%) — modo conservador")
    elif ibov <= -1.0:
        score = 0.30
        reasons.append(f"Macro: Ibovespa em queda ({ibov:+.2f}%)")
    else:
        score = 0.55
        reasons.append(f"Macro: Ibovespa neutro ({ibov:+.2f}%)")

    return round(score, 3), reasons


def _quality_filters(fm: FundamentalMetrics) -> tuple[bool, list[str]]:
    failures = []

    price = fm.current_price or 0.0
    vol = fm.avg_volume_10d or 0
    daily_vol_brl = vol * price
    if daily_vol_brl < _MIN_DAILY_VOLUME_BRL:
        failures.append(
            f"Volume médio diário R${daily_vol_brl:,.0f} < mínimo R${_MIN_DAILY_VOLUME_BRL:,.0f}"
        )

    cap = fm.market_cap_brl or 0.0
    if cap < _MIN_MARKET_CAP_BRL:
        failures.append(
            f"Market cap R${cap:,.0f} < mínimo R${_MIN_MARKET_CAP_BRL:,.0f}"
        )

    return len(failures) == 0, failures


async def score_ticker(
    ticker: str,
    macro_context: MacroContext | None = None,
) -> ScoreResult:
    """
    Score combinado para decisão de compra em um ticker B3.

    Fetches técnica, fundamental e sentimento em paralelo.
    Aplica filtros de qualidade como gate hard antes do score.

    Args:
        ticker: símbolo B3, ex: "PETR4"
        macro_context: contexto macro já carregado (evita nova chamada BCB)

    Returns:
        ScoreResult com score 0-1, breakdown, recomendação e razões
    """
    technical, fundamental, sentiment, macro = await asyncio.gather(
        detect_patterns_async(ticker),
        parse_quarterly_earnings_async(ticker),
        analyze_sentiment(ticker),
        load_macro_context() if macro_context is None else _noop(macro_context),
    )

    passes, filter_failures = _quality_filters(fundamental)

    tech_score, tech_reasons = _technical_score(technical)
    fund_score, fund_reasons = _fundamental_score(fundamental)
    sent_score, sent_reasons = _sentiment_score(sentiment)
    macro_score, macro_reasons = _macro_score(macro)

    combined = round(
        0.40 * tech_score +
        0.40 * fund_score +
        0.10 * sent_score +
        0.10 * macro_score,
        3,
    )

    if not passes:
        recommendation = "skip"
    elif combined >= _BUY_THRESHOLD:
        recommendation = "buy"
    elif combined >= _HOLD_THRESHOLD:
        recommendation = "hold"
    else:
        recommendation = "skip"

    all_reasons = tech_reasons + fund_reasons + sent_reasons + macro_reasons

    return ScoreResult(
        ticker=ticker,
        timestamp=datetime.now(timezone.utc).isoformat(),
        score=ScoreBreakdown(
            technical=tech_score,
            fundamental=fund_score,
            sentiment=sent_score,
            macro=macro_score,
            combined=combined,
        ),
        passes_quality_filters=passes,
        quality_filter_failures=filter_failures,
        recommendation=recommendation,
        reasons=all_reasons,
        technical_signal=technical.model_dump(),
        fundamental_metrics=fundamental.model_dump(),
    )


async def score_watchlist(
    tickers: list[str],
    macro_context: MacroContext | None = None,
) -> list[ScoreResult]:
    """Score todos os tickers da watchlist em paralelo, ordena por score desc."""
    if macro_context is None:
        macro_context = await load_macro_context()

    results = await asyncio.gather(
        *[score_ticker(t, macro_context) for t in tickers],
        return_exceptions=True,
    )

    valid = [r for r in results if isinstance(r, ScoreResult)]
    valid.sort(key=lambda r: r.score.combined, reverse=True)
    return valid


async def _noop(val):
    return val
