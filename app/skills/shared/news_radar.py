"""
Market news radar — scans RSS feeds and identifies B3 tickers by news volume + sentiment.

Two-pass ticker extraction:
  1. Regex `(TICKER)` pattern — Brazilian financial news routinely includes tickers in parentheses.
     Most reliable signal; zero false positives.
  2. Alias dictionary — company names for sources that don't include ticker symbols.
     Conservative: only unambiguous multi-word names (no "Vale" or "B3" standalone).

Reuses _fetch_rss and _score_text from sentiment.py.
"""
import asyncio
import re
from typing import Optional

import httpx

from app.skills.shared.sentiment import _fetch_rss, _score_text

# Feeds focused on B3 stocks — include ticker symbols in headlines
_RADAR_FEEDS = {
    "moneytimes": "https://moneytimes.com.br/feed/",
    "suno":       "https://www.suno.com.br/noticias/feed/",
    "infomoney":  "https://www.infomoney.com.br/feed/",
    "investing_br": "https://br.investing.com/rss/news.rss",
}

# Watchlist base (18 tickers validados no Brapi)
_BASE_WATCHLIST = {
    "VALE3", "ITUB4", "PETR4", "B3SA3", "SBSP3", "ABEV3", "WEGE3", "BBAS3",
    "PRIO3", "EMBJ3", "EQTL3", "RENT3", "VIVT3", "SUZB3", "CMIG4",
    "RDOR3", "BBDC4", "GGBR4",
}

# ticker → list of unambiguous aliases for PT-BR financial news matching.
# Rules:
#   - No single-word aliases that are common Portuguese words (vale, banco, vivo, etc.)
#   - Short aliases (< 5 chars) only allowed if they're clear ticker symbols
#   - Ambiguous aliases removed (B3 alone, BB alone, Vale alone)
_TICKER_ALIASES: dict[str, list[str]] = {
    # --- Watchlist base ---
    "VALE3":  ["Vale S.A", "Vale S/A", "VALE3", "mineradora Vale", "Vale ON"],
    "ITUB4":  ["Itaú Unibanco", "Itauunibanco", "ITUB4", "Itaú S.A"],
    "PETR4":  ["Petrobras", "Petróleo Brasileiro", "PETR4"],
    "PETR3":  ["Petrobras", "Petróleo Brasileiro", "PETR3"],
    "B3SA3":  ["B3 S.A", "B3SA3", "B3 anuncia", "B3 reporta"],
    "SBSP3":  ["Sabesp", "SBSP3", "Companhia de Saneamento Básico"],
    "ABEV3":  ["Ambev", "AmBev", "ABEV3"],
    "WEGE3":  ["WEG S.A", "Weg S.A", "WEGE3"],
    "BBAS3":  ["Banco do Brasil", "BBAS3"],
    "PRIO3":  ["PetroRio", "Petro Rio", "PRIO3", "Prio S.A"],
    "EMBJ3":  ["Embraer", "EMBJ3"],
    "EQTL3":  ["Equatorial Energia", "EQTL3"],
    "RENT3":  ["Localiza", "RENT3", "Localiza Hertz"],
    "VIVT3":  ["Telefônica Brasil", "Telefonica Brasil", "VIVT3"],
    "SUZB3":  ["Suzano", "SUZB3", "Suzano S.A"],
    "CMIG4":  ["Cemig", "CMIG4"],
    "RDOR3":  ["Rede D'Or", "Rede D Or", "RDOR3"],
    "BBDC4":  ["Bradesco", "BBDC4", "Banco Bradesco"],
    "GGBR4":  ["Gerdau", "GGBR4"],
    # --- Ibovespa fora da watchlist (oportunidades externas) ---
    "MGLU3":  ["Magazine Luiza", "Magalu", "MGLU3"],
    "LREN3":  ["Lojas Renner", "LREN3"],
    "AZUL4":  ["Azul Linhas", "Azul S.A", "AZUL4"],
    "CSAN3":  ["Cosan", "CSAN3"],
    "BPAC11": ["BTG Pactual", "BPAC11"],
    "VBBR3":  ["Vibra Energia", "VBBR3"],
    "UGPA3":  ["Ultrapar", "UGPA3"],
    "RADL3":  ["Raia Drogasil", "RADL3"],
    "TIMS3":  ["TIM Brasil", "TIMS3"],
    "ENEV3":  ["Eneva", "ENEV3"],
    "ITSA4":  ["Itaúsa", "Itausa", "ITSA4"],
    "CPLE3":  ["Copel", "CPLE3"],
    "BBSE3":  ["BB Seguridade", "BBSE3"],
    "HAPV3":  ["Hapvida", "HAPV3"],
    "PSSA3":  ["Porto Seguro", "PSSA3"],
    "RECV3":  ["PetroRecôncavo", "PetroReconcavo", "RECV3"],
    "BRAV3":  ["Brava Energia", "BRAV3"],
    "SMTO3":  ["São Martinho", "Sao Martinho", "SMTO3"],
    "YDUQ3":  ["Yduqs", "YDUQ3"],
    "BRFS3":  ["BRF", "BRFS3", "BRF S.A"],
    "JBSS3":  ["JBS", "JBSS3", "JBS S.A"],
}

# Deduplicate: some tickers share aliases (PETR3/PETR4 both match "Petrobras").
# When an article matches multiple tickers via shared alias,
# prefer the one in the base watchlist; if both are, keep both.
_SHARED_ALIASES: dict[str, list[str]] = {
    "Petrobras": ["PETR4", "PETR3"],
}


# Regex: tickers in parentheses, e.g. (PETR4), (BPAC11) — primary signal
_TICKER_IN_PARENS = re.compile(r"\(([A-Z]{4}[0-9]{1,2})\)")

# Known B3 tickers for validation (avoid matching random strings like (BRL1))
_KNOWN_TICKERS: set[str] = set(_TICKER_ALIASES.keys())


def _find_tickers_in_text(text: str) -> set[str]:
    found: set[str] = set()

    # Pass 1: regex on parenthesised tickers — most reliable
    for match in _TICKER_IN_PARENS.finditer(text):
        candidate = match.group(1)
        if candidate in _KNOWN_TICKERS:
            found.add(candidate)

    # Pass 2: alias dictionary — for sources that don't use (TICKER) pattern
    for ticker, aliases in _TICKER_ALIASES.items():
        if ticker in found:
            continue  # already found via parens
        for alias in aliases:
            if re.search(rf"\b{re.escape(alias)}\b", text, re.IGNORECASE):
                found.add(ticker)
                break

    # Deduplicate: PETR3 and PETR4 share "Petrobras" alias — keep only PETR4 (more liquid)
    if "PETR4" in found and "PETR3" in found:
        found.discard("PETR3")

    return found


async def scan_market_news(max_results: int = 15) -> list[dict]:
    """
    Scan RSS feeds and return B3 tickers ranked by news volume × sentiment strength.

    Args:
        max_results: Max tickers to return (default 15).

    Returns:
        List of dicts sorted by relevance score (mentions × |sentiment|):
          ticker, mentions, sentiment_score, sentiment_label,
          headlines (up to 3), in_watchlist (bool)
    """
    async with httpx.AsyncClient(
        headers={"User-Agent": "Mozilla/5.0 investimentos-ai/1.0"},
        follow_redirects=True,
    ) as client:
        feed_results = await asyncio.gather(
            *[_fetch_rss(url, client) for url in _RADAR_FEEDS.values()],
            return_exceptions=True,
        )

    all_items: list[dict] = []
    for r in feed_results:
        if isinstance(r, list):
            all_items.extend(r)

    ticker_data: dict[str, dict] = {}

    for item in all_items:
        full_text = f"{item['title']} {item.get('description', '')}"
        tickers_in_article = _find_tickers_in_text(full_text)
        if not tickers_in_article:
            continue

        score = _score_text(full_text)

        for ticker in tickers_in_article:
            if ticker not in ticker_data:
                ticker_data[ticker] = {"mentions": 0, "scores": [], "headlines": []}
            ticker_data[ticker]["mentions"] += 1
            ticker_data[ticker]["scores"].append(score)
            if len(ticker_data[ticker]["headlines"]) < 3:
                headline = item["title"].strip()
                if headline and headline not in ticker_data[ticker]["headlines"]:
                    ticker_data[ticker]["headlines"].append(headline)

    output: list[dict] = []
    for ticker, data in ticker_data.items():
        avg_sentiment = round(sum(data["scores"]) / len(data["scores"]), 3)
        label = (
            "positive" if avg_sentiment > 0.1
            else ("negative" if avg_sentiment < -0.1 else "neutral")
        )
        relevance = round(data["mentions"] * (0.5 + abs(avg_sentiment)), 3)
        output.append({
            "ticker": ticker,
            "mentions": data["mentions"],
            "sentiment_score": avg_sentiment,
            "sentiment_label": label,
            "relevance_score": relevance,
            "headlines": data["headlines"],
            "in_watchlist": ticker in _BASE_WATCHLIST,
        })

    output.sort(key=lambda x: x["relevance_score"], reverse=True)
    return output[:max_results]
