import json
import time
from typing import Optional

import httpx
import redis.asyncio as aioredis

from app.config import get_settings

# In-memory fallback cache: {key: (data, timestamp)}
_mem_cache: dict[str, tuple[dict, float]] = {}
_redis_client: Optional[aioredis.Redis] = None


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
    return "hg:quotes:" + ",".join(sorted(tickers)) + (f":{sort}" if sort else "")


async def get_quotes(tickers: list[str], sort: Optional[str] = None) -> dict:
    settings = get_settings()
    key = _cache_key(tickers, sort)
    ttl = settings.cache_ttl_seconds

    # Try Redis first
    redis = await _get_redis()
    if redis:
        try:
            cached = await redis.get(key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass

    # Try in-memory cache
    if key in _mem_cache:
        data, ts = _mem_cache[key]
        if time.time() - ts < ttl:
            return data

    params: dict = {"key": settings.hgbrasil_api_key, "tickers": ",".join(tickers)}
    if sort:
        params["sort"] = sort

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(settings.hgbrasil_base_url, params=params)
        response.raise_for_status()
        data = response.json()

    # Write to Redis
    if redis:
        try:
            await redis.setex(key, ttl, json.dumps(data))
        except Exception:
            pass

    # Write to in-memory fallback
    _mem_cache[key] = (data, time.time())

    return data
