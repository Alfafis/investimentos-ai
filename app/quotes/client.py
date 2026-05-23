import asyncio
import json
import time
from typing import Optional

import httpx
import yfinance as yf
import redis.asyncio as aioredis

from app.config import get_settings

_mem_cache: dict[str, tuple[dict, float]] = {}
_redis_client: Optional[aioredis.Redis] = None

_BRAPI_BASE = "https://brapi.dev/api"


async def _get_redis() -> Optional[aioredis.Redis]:
    global _redis_client
    if _redis_client is None:
        try:
            settings = get_settings()
            client = aioredis.from_url(settings.redis_url, decode_responses=True)
            await client.ping()
            _redis_client = client
        except Exception:
            _redis_client = None
    return _redis_client


def _cache_key(tickers: list[str], sort: Optional[str]) -> str:
    return "quotes:" + ",".join(sorted(tickers)) + (f":{sort}" if sort else "")


def _b3_to_symbol(ticker: str) -> str:
    t = ticker.upper()
    if t.startswith("B3:"):
        t = t[3:]
    return t


def _b3_to_yf(ticker: str) -> str:
    sym = _b3_to_symbol(ticker)
    return sym if sym.endswith(".SA") else sym + ".SA"


# ---------------------------------------------------------------------------
# Brapi (primary)
# ---------------------------------------------------------------------------

async def _fetch_brapi_batch(symbols: list[str]) -> dict[str, dict]:
    """Batch quote fetch from Brapi. Returns {symbol: raw_item}."""
    settings = get_settings()
    if not settings.brapi_api_key:
        return {}

    tickers_str = ",".join(symbols)
    url = f"{_BRAPI_BASE}/quote/{tickers_str}"
    params = {
        "token": settings.brapi_api_key,
        "fundamental": "true",
        "dividends": "true",
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
        return {item["symbol"]: item for item in data.get("results", []) if item.get("symbol")}
    except Exception:
        return {}


def _brapi_to_quote(item: dict) -> dict:
    sym = item["symbol"]
    price = item.get("regularMarketPrice") or 0.0
    change_val = item.get("regularMarketChange") or 0.0
    change_pct = item.get("regularMarketChangePercent") or 0.0

    # Brapi returns dividendYield as percentage already (e.g. 8.72 = 8.72%)
    raw_dy = item.get("dividendYield")
    dy_pct = round(raw_dy, 2) if raw_dy else None
    dy_cash = round(raw_dy / 100 * price, 4) if raw_dy and price else None

    updated = item.get("regularMarketTime") or time.strftime("%Y-%m-%dT%H:%M:%S")

    return {
        "ticker": f"B3:{sym}",
        "symbol": sym,
        "name": item.get("longName") or item.get("shortName") or sym,
        "full_name": item.get("longName"),
        "kind": "stock",
        "currency": item.get("currency", "BRL"),
        "classification": None,
        "quote": {
            "value": round(price, 2),
            "change_value": round(change_val, 4),
            "change_percent": round(change_pct, 4),
            "market_cap": item.get("marketCap"),
            "updated_at": updated,
        },
        "dividends": {
            "yield_12m_percent": dy_pct,
            "yield_12m_cash": dy_cash,
        } if dy_pct is not None else None,
    }


# ---------------------------------------------------------------------------
# yfinance (fallback)
# ---------------------------------------------------------------------------

def _fetch_yf_quote(yf_ticker: str) -> dict | None:
    try:
        t = yf.Ticker(yf_ticker)
        fi = t.fast_info
        info = t.info or {}

        symbol = yf_ticker.removesuffix(".SA")
        last_price = fi.last_price or 0.0
        prev_close = fi.previous_close or 0.0
        change_value = last_price - prev_close
        change_pct = round(change_value / prev_close * 100, 4) if prev_close else 0.0

        raw_dy = info.get("dividendYield") or info.get("trailingAnnualDividendYield")
        dy_pct = round(raw_dy, 2) if raw_dy else None
        dy_cash = round(raw_dy / 100 * last_price, 4) if raw_dy and last_price else None

        return {
            "ticker": f"B3:{symbol}",
            "symbol": symbol,
            "name": info.get("shortName") or info.get("longName") or symbol,
            "full_name": info.get("longName"),
            "kind": "stock",
            "currency": "BRL",
            "classification": None,
            "quote": {
                "value": round(last_price, 2),
                "change_value": round(change_value, 4),
                "change_percent": change_pct,
                "market_cap": fi.market_cap,
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            },
            "dividends": {
                "yield_12m_percent": dy_pct,
                "yield_12m_cash": dy_cash,
            } if dy_pct is not None else None,
        }
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Sort + main entry
# ---------------------------------------------------------------------------

_SORT_KEY = {
    "value": lambda x: (x.get("quote") or {}).get("value") or 0.0,
    "change_percent": lambda x: (x.get("quote") or {}).get("change_percent") or 0.0,
}


def _apply_sort(results: list[dict], sort: Optional[str]) -> list[dict]:
    if not sort:
        return results
    parts = sort.split(":")
    fn = _SORT_KEY.get(parts[0])
    if not fn:
        return results
    return sorted(results, key=fn, reverse=(len(parts) < 2 or parts[1] == "desc"))


async def get_quotes(tickers: list[str], sort: Optional[str] = None) -> dict:
    settings = get_settings()
    key = _cache_key(tickers, sort)
    ttl = settings.cache_ttl_seconds

    redis = await _get_redis()
    if redis:
        try:
            cached = await redis.get(key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass

    if key in _mem_cache:
        data, ts = _mem_cache[key]
        if time.time() - ts < ttl:
            return data

    symbols = [_b3_to_symbol(t) for t in tickers]

    # 1. Try Brapi batch
    brapi_map = await _fetch_brapi_batch(symbols)

    results = []
    yf_fallback = []

    for sym in symbols:
        if sym in brapi_map:
            results.append(_brapi_to_quote(brapi_map[sym]))
        else:
            yf_fallback.append(sym)

    # 2. yfinance fallback for any missed tickers
    if yf_fallback:
        yf_tickers = [s + ".SA" for s in yf_fallback]
        raw = await asyncio.gather(*[asyncio.to_thread(_fetch_yf_quote, t) for t in yf_tickers])
        results.extend([r for r in raw if r is not None])

    results = _apply_sort(results, sort)

    data = {
        "metadata": {
            "cached": False,
            "response_time_ms": 0.0,
            "language": "pt-br",
            "source": "brapi" if brapi_map else "yfinance",
        },
        "results": results,
    }

    if redis:
        try:
            await redis.setex(key, ttl, json.dumps(data))
        except Exception:
            pass

    _mem_cache[key] = (data, time.time())
    return data
