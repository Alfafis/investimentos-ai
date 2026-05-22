"""
news_sentiment_analysis — RSS feeds + keyword scoring for PT-BR financial news.

Default: fast keyword-based scoring (no model download required).
Sources: InfoMoney RSS, Valor Econômico (when available).

Score range: -1.0 (very negative) to +1.0 (very positive).
"""
import asyncio
import re
from datetime import datetime, timezone
from typing import Optional

import httpx

from app.models import NewsItem, SentimentResult

_RSS_FEEDS = {
    "infomoney": "https://www.infomoney.com.br/feed/",
    "investing_br": "https://br.investing.com/rss/news.rss",
}

# PT-BR financial sentiment lexicon
_POSITIVE = {
    "alta", "subiu", "sobe", "valorização", "lucro", "crescimento", "recorde",
    "positivo", "forte", "elevou", "ganho", "expansão", "melhora", "supera",
    "acima", "compra", "recomenda", "upgrade", "outperform", "dividendo",
    "resultado", "bom", "otimismo", "recuperação", "aprovado", "contrato",
    "parceria", "investimento", "aumento", "superou", "bateu",
}

_NEGATIVE = {
    "queda", "caiu", "cai", "desvalorização", "prejuízo", "perda", "fraco",
    "negativo", "redução", "corte", "abaixo", "venda", "downgrade", "underperform",
    "risco", "incerteza", "crise", "pressão", "preocupação", "alerta", "piora",
    "perde", "derreteu", "despencou", "colapso", "falência", "multa", "investigação",
    "fraude", "cancelado", "atraso", "rombo", "déficit",
}


def _score_text(text: str) -> float:
    words = set(re.findall(r"\b\w+\b", text.lower()))
    pos = len(words & _POSITIVE)
    neg = len(words & _NEGATIVE)
    total = pos + neg
    if total == 0:
        return 0.0
    return round((pos - neg) / total, 3)


def _ticker_in_text(ticker: str, text: str) -> bool:
    return bool(re.search(rf"\b{re.escape(ticker)}\b", text, re.IGNORECASE))


async def _fetch_rss(url: str, client: httpx.AsyncClient) -> list[dict]:
    try:
        r = await client.get(url, timeout=8.0)
        r.raise_for_status()
        # Simple RSS XML parser (avoid feedparser dependency in Docker)
        import xml.etree.ElementTree as ET
        root = ET.fromstring(r.text)
        items = []
        ns = ""
        for item in root.iter("item"):
            title = item.findtext("title") or ""
            desc = item.findtext("description") or ""
            link = item.findtext("link") or ""
            pub_date = item.findtext("pubDate") or ""
            items.append({"title": title, "description": desc, "link": link, "pub_date": pub_date})
        return items[:20]  # cap at 20 per feed
    except Exception:
        return []


async def analyze_sentiment(
    ticker: str,
    max_articles: int = 10,
) -> SentimentResult:
    """
    Fetch recent financial news and score sentiment for a ticker.

    Args:
        ticker: B3 symbol, e.g. "PETR4"
        max_articles: Max articles to consider per source

    Returns:
        SentimentResult with score, relevant headlines, and article count
    """
    company_name = ticker[:4]  # fallback — improve with lookup table later

    async with httpx.AsyncClient(
        headers={"User-Agent": "Mozilla/5.0 investimentos-ai/1.0"},
        follow_redirects=True,
    ) as client:
        results = await asyncio.gather(
            *[_fetch_rss(url, client) for url in _RSS_FEEDS.values()],
            return_exceptions=True,
        )

    all_items = []
    for r in results:
        if isinstance(r, list):
            all_items.extend(r)

    relevant: list[NewsItem] = []
    scores: list[float] = []

    for item in all_items:
        full_text = f"{item['title']} {item['description']}"
        if not _ticker_in_text(ticker, full_text) and not _ticker_in_text(company_name, full_text):
            continue
        score = _score_text(full_text)
        relevant.append(NewsItem(
            title=item["title"].strip(),
            source=item.get("link", "")[:60],
            pub_date=item.get("pub_date", ""),
            sentiment_score=score,
        ))
        scores.append(score)

    # Include general market news if no ticker-specific found
    if not relevant:
        for item in all_items[:5]:
            full_text = f"{item['title']} {item['description']}"
            score = _score_text(full_text)
            scores.append(score)

    avg_score = round(sum(scores) / len(scores), 3) if scores else 0.0
    label = "positive" if avg_score > 0.1 else ("negative" if avg_score < -0.1 else "neutral")

    return SentimentResult(
        ticker=ticker,
        score=avg_score,
        label=label,
        articles_analyzed=len(scores),
        relevant_headlines=relevant[:max_articles],
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
