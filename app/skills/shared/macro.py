"""
macro_context_loader — BCB API (free, no key required).

Provides: Selic, IPCA, USD/BRL PTax, Ibovespa, B3 market status.
"""
from datetime import date, datetime
from zoneinfo import ZoneInfo

import httpx

from app.models import MacroContext

_BCB = "https://api.bcb.gov.br/dados/serie/bcdata.sgs"
_PTAX = "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata"
_BRT = ZoneInfo("America/Sao_Paulo")

# B3 public holidays 2026 (ISO format) — update annually
_B3_HOLIDAYS_2026 = {
    "2026-01-01", "2026-02-16", "2026-02-17", "2026-04-03",
    "2026-04-21", "2026-05-01", "2026-06-04", "2026-09-07",
    "2026-10-12", "2026-11-02", "2026-11-15", "2026-11-20",
    "2026-12-24", "2026-12-25", "2026-12-31",
}


def _is_market_open() -> bool:
    now = datetime.now(_BRT)
    today_str = now.strftime("%Y-%m-%d")
    if now.weekday() >= 5:  # Saturday/Sunday
        return False
    if today_str in _B3_HOLIDAYS_2026:
        return False
    market_open = now.replace(hour=10, minute=0, second=0, microsecond=0)
    market_close = now.replace(hour=17, minute=55, second=0, microsecond=0)
    return market_open <= now <= market_close


async def _bcb_latest(series_id: int) -> float | None:
    url = f"{_BCB}.{series_id}/dados/ultimos/1?formato=json"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()
            return float(data[0]["valor"]) if data else None
    except Exception:
        return None


async def _ptax_usd() -> float | None:
    # Use BRT date (not UTC) — BCB publishes by Brazil business day.
    # Try up to 5 previous days to handle weekends and holidays.
    from datetime import timedelta
    brt_today = datetime.now(_BRT).date()
    async with httpx.AsyncClient(timeout=8.0) as client:
        for days_back in range(5):
            candidate = brt_today - timedelta(days=days_back)
            date_str = candidate.strftime("%m-%d-%Y")
            url = (
                f"{_PTAX}/CotacaoDolarDia(dataCotacao=@d)"
                f"?@d='{date_str}'&$top=1&$format=json&$select=cotacaoVenda"
            )
            try:
                r = await client.get(url)
                r.raise_for_status()
                items = r.json().get("value", [])
                if items:
                    return float(items[0]["cotacaoVenda"])
            except Exception:
                continue
    return None


async def _ibovespa_change() -> float | None:
    try:
        import asyncio
        import pandas as pd
        import yfinance as yf

        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(
            None,
            lambda: yf.download("^BVSP", period="2d", auto_adjust=True, progress=False),
        )
        if df.empty or len(df) < 2:
            return None
        closes = df["Close"].dropna()
        if isinstance(closes, pd.DataFrame):
            closes = closes.iloc[:, 0]
        prev, last = float(closes.iloc[-2]), float(closes.iloc[-1])
        return round((last - prev) / prev * 100, 2)
    except Exception:
        return None


async def load_macro_context() -> MacroContext:
    """
    Fetch macro snapshot: Selic, IPCA, USD/BRL, Ibovespa, market status.
    Non-blocking — missing data fields return None gracefully.
    """
    import asyncio

    selic, ipca, usd, ibov = await asyncio.gather(
        _bcb_latest(11),      # Selic diária (% a.a.)
        _bcb_latest(13522),   # IPCA mensal acumulado 12m
        _ptax_usd(),
        _ibovespa_change(),
    )

    return MacroContext(
        market_open=_is_market_open(),
        selic_rate=selic,
        usd_brl=usd,
        ipca_12m=ipca,
        ibovespa_change_pct=ibov,
        timestamp=datetime.now(_BRT).isoformat(),
    )
