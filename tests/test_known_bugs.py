"""Bugs conhecidos, registrados como xfail(strict=True). NÃO corrigir aqui:
quando o bug for corrigido o teste passa a XPASS e quebra a suíte (strict),
sinalizando que o marcador deve ser removido."""
import pytest


@pytest.mark.xfail(strict=True, reason=(
    "BUG: sell sem posição aberta é aceito e gravado; get_trade_outcomes soma o "
    "proceeds ao caixa, inflando cash_balance_brl sem nada ter sido comprado."
))
def test_sell_without_open_position_is_rejected(store):
    try:
        store.save_paper_trade("sell", "PETR4", 30.0, 10, session_id="s1")
    except ValueError:
        return  # rejeitar é o comportamento esperado
    out = store.get_trade_outcomes(initial_capital=5000.0)
    assert out["cash_balance_brl"] <= 5000.0


@pytest.mark.xfail(strict=True, reason=(
    "BUG: 'PETR4' e 'PETR4.SA' são gravados como tickers distintos (só upper() é aplicado), "
    "gerando chaves de idempotência diferentes, posições separadas e duplicata não detectada."
))
def test_petr4_and_petr4_sa_are_same_ticker(store):
    a = store.save_paper_trade("buy", "PETR4", 30.0, 10, session_id="s1")
    b = store.save_paper_trade("buy", "PETR4.SA", 30.0, 10, session_id="s1")
    assert b.created is False and b.id == a.id
    assert len(store.get_paper_portfolio()) == 1
