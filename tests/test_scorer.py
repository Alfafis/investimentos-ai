import asyncio

import pytest

from app.models import FundamentalMetrics, MacroContext, SentimentResult, TechnicalSignal
from app.skills.shared import scorer


def tech(signal="buy", conf=0.8, ema200=None):
    return TechnicalSignal(
        ticker="PETR4", timestamp="t", signal=signal, confidence=conf,
        reasons=[], ema_200=ema200,
    )


def fund(**kw):
    base = dict(
        ticker="PETR4", pe_ratio=10, roe=20, debt_equity=1.0, dividend_yield=5,
        upside_pct=30, current_price=30.0, avg_volume_10d=1_000_000,
        market_cap_brl=1_000_000_000,
    )
    base.update(kw)
    return FundamentalMetrics(**base)


def sent(score=0.0, label="neutral", n=3):
    return SentimentResult(
        ticker="PETR4", score=score, label=label, articles_analyzed=n,
        relevant_headlines=[], timestamp="t",
    )


def macro(ibov=0.0):
    return MacroContext(market_open=True, ibovespa_change_pct=ibov, timestamp="t")


@pytest.fixture
def run(monkeypatch):
    """Executa score_ticker com as 4 fontes mockadas (sem rede)."""
    def _run(t, f, s, m):
        async def _t(*a, **k): return t
        async def _f(*a, **k): return f
        async def _s(*a, **k): return s
        async def _m(*a, **k): return m
        monkeypatch.setattr(scorer, "detect_patterns_async", _t)
        monkeypatch.setattr(scorer, "parse_quarterly_earnings_async", _f)
        monkeypatch.setattr(scorer, "analyze_sentiment", _s)
        monkeypatch.setattr(scorer, "load_macro_context", _m)
        return asyncio.run(scorer.score_ticker("PETR4"))
    return _run


# ----------------------------------------------------------- componentes

def test_technical_score_mapping():
    assert scorer._technical_score(tech("buy", 0.8))[0] == 0.8
    assert scorer._technical_score(tech("sell", 0.8))[0] == pytest.approx(0.2)
    assert scorer._technical_score(tech("hold", 0.9))[0] == 0.5


def test_fundamental_score_counts_five_checks():
    assert scorer._fundamental_score(fund())[0] == 1.0
    assert scorer._fundamental_score(fund(pe_ratio=25))[0] == 0.8
    assert scorer._fundamental_score(fund(pe_ratio=25, roe=5))[0] == 0.6


def test_fundamental_score_all_missing_is_zero():
    fm = FundamentalMetrics(ticker="X")
    score, reasons = scorer._fundamental_score(fm)
    assert score == 0.0 and reasons == []


def test_sentiment_score_rescales_to_0_1():
    assert scorer._sentiment_score(sent(-1.0))[0] == 0.0
    assert scorer._sentiment_score(sent(0.0))[0] == 0.5
    assert scorer._sentiment_score(sent(1.0))[0] == 1.0


@pytest.mark.parametrize("ibov,expected", [
    (1.0, 0.75), (2.5, 0.75), (0.0, 0.55), (-0.99, 0.55),
    (-1.0, 0.30), (-2.9, 0.30), (-3.0, 0.10), (-5.0, 0.10), (None, 0.55),
])
def test_macro_score_buckets(ibov, expected):
    ctx = MacroContext(market_open=True, ibovespa_change_pct=ibov, timestamp="t")
    assert scorer._macro_score(ctx)[0] == expected


def test_quality_filters():
    ok, fails = scorer._quality_filters(fund())
    assert ok and fails == []
    ok, fails = scorer._quality_filters(fund(avg_volume_10d=1000))  # 30k < 5M
    assert not ok and len(fails) == 1 and "Volume" in fails[0]
    ok, fails = scorer._quality_filters(fund(market_cap_brl=1e8))
    assert not ok and "Market cap" in fails[0]


# ----------------------------------------------------------- score_ticker

def test_weights_40_40_10_10(run):
    # tech 0.8, fund 1.0, sent 1.0, macro 0.75
    r = run(tech("buy", 0.8), fund(), sent(1.0, "positive"), macro(2.0))
    b = r.score
    assert (b.technical, b.fundamental, b.sentiment, b.macro) == (0.8, 1.0, 1.0, 0.75)
    assert b.combined == round(0.4 * 0.8 + 0.4 * 1.0 + 0.1 * 1.0 + 0.1 * 0.75, 3) == 0.895
    assert r.recommendation == "buy"
    assert r.passes_quality_filters


def test_weights_isolated_per_component(run):
    # tudo zerado exceto um componente por vez
    low_t = tech("sell", 1.0)                       # técnica 0.0
    low_f = fund(pe_ratio=99, roe=0, debt_equity=9, dividend_yield=0, upside_pct=0)  # 0.0
    r = run(tech("buy", 1.0), low_f, sent(-1.0), macro(-5.0))
    assert r.score.combined == pytest.approx(0.4 * 1.0 + 0.0 + 0.0 + 0.1 * 0.10, abs=1e-3)
    r = run(low_t, fund(), sent(-1.0), macro(-5.0))
    assert r.score.combined == pytest.approx(0.0 + 0.4 + 0.0 + 0.01, abs=1e-3)


def test_thresholds_buy_hold_skip(run):
    # combined = 0.4*0.5 + 0.4*f + 0.1*0.5 + 0.1*0.55
    hold = run(tech("hold"), fund(pe_ratio=25, roe=5), sent(0.0), macro(0.0))   # f=0.6
    assert hold.score.combined == pytest.approx(0.545, abs=1e-3)
    assert hold.recommendation == "hold"
    skip = run(tech("hold"), fund(pe_ratio=99, roe=0, debt_equity=9, dividend_yield=0, upside_pct=0),
               sent(0.0), macro(0.0))
    assert skip.score.combined < 0.40 and skip.recommendation == "skip"


def test_quality_filter_failure_forces_skip_even_with_high_score(run):
    r = run(tech("buy", 1.0), fund(avg_volume_10d=10), sent(1.0), macro(2.0))
    assert r.score.combined >= 0.6
    assert r.recommendation == "skip"
    assert not r.passes_quality_filters and r.quality_filter_failures


def test_ema200_hard_veto(run):
    r = run(tech("buy", 1.0, ema200=35.0), fund(current_price=30.0), sent(1.0), macro(2.0))
    assert r.recommendation == "skip"
    assert any("EMA200" in f for f in r.quality_filter_failures)


def test_price_above_ema200_no_veto(run):
    r = run(tech("buy", 1.0, ema200=25.0), fund(current_price=30.0), sent(1.0), macro(2.0))
    assert r.recommendation == "buy"


# ------------------------------------------------------------ dado faltante

def test_missing_fundamentals_skips_with_filter_failures(run):
    r = run(tech("buy", 1.0), FundamentalMetrics(ticker="PETR4"), sent(0.0), macro(0.0))
    assert r.score.fundamental == 0.0
    assert r.recommendation == "skip"
    assert len(r.quality_filter_failures) == 2  # volume e market cap


def test_missing_macro_uses_neutral(run):
    r = run(tech("hold"), fund(), sent(0.0), MacroContext(market_open=False, timestamp="t"))
    assert r.score.macro == 0.55


def test_missing_ema200_does_not_veto(run):
    r = run(tech("buy", 1.0, ema200=None), fund(), sent(1.0), macro(2.0))
    assert r.passes_quality_filters and r.recommendation == "buy"


def test_missing_price_no_veto_but_fails_volume(run):
    r = run(tech("buy", 1.0, ema200=35.0), fund(current_price=None), sent(1.0), macro(2.0))
    assert r.recommendation == "skip"
    assert not any("EMA200" in f for f in r.quality_filter_failures)


def test_provided_macro_context_skips_loader(monkeypatch):
    async def _t(*a, **k): return tech("hold")
    async def _f(*a, **k): return fund()
    async def _s(*a, **k): return sent()
    async def boom(*a, **k): raise AssertionError("não deveria chamar load_macro_context")
    monkeypatch.setattr(scorer, "detect_patterns_async", _t)
    monkeypatch.setattr(scorer, "parse_quarterly_earnings_async", _f)
    monkeypatch.setattr(scorer, "analyze_sentiment", _s)
    monkeypatch.setattr(scorer, "load_macro_context", boom)
    r = asyncio.run(scorer.score_ticker("PETR4", macro_context=macro(2.0)))
    assert r.score.macro == 0.75
