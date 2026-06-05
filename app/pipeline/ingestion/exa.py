"""Exa neural-search provider (optional, requires EXA_API_KEY).

Enabled with ``SEARCH_PROVIDER=exa``.
"""

from __future__ import annotations

import logging
from datetime import datetime

import httpx

from app.pipeline.ingestion.base import RawArticle, SearchProvider

logger = logging.getLogger(__name__)

EXA_SEARCH_URL = "https://api.exa.ai/search"


class ExaSearchProvider(SearchProvider):
    def __init__(self, api_key: str, timeout: float = 30.0):
        self.api_key = api_key
        self.timeout = timeout

    def search(self, queries: list[str], limit: int) -> list[RawArticle]:
        articles: list[RawArticle] = []
        seen: set[str] = set()
        per_query = max(1, limit // max(1, len(queries)))
        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}

        with httpx.Client(timeout=self.timeout) as client:
            for query in queries:
                try:
                    resp = client.post(
                        EXA_SEARCH_URL,
                        headers=headers,
                        json={
                            "query": query,
                            "numResults": per_query,
                            "type": "auto",
                            "contents": {"text": {"maxCharacters": 500}},
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as exc:
                    logger.warning("Exa search failed for %r: %s", query, exc)
                    continue

                for item in data.get("results", []):
                    url = (item.get("url") or "").strip()
                    title = (item.get("title") or "").strip()
                    if not url or not title or url in seen:
                        continue
                    seen.add(url)
                    articles.append(
                        RawArticle(
                            url=url,
                            title=title,
                            snippet=(item.get("text") or "")[:500],
                            published_at=_parse_date(item.get("publishedDate")),
                            raw_meta={"query": query, "provider": "exa"},
                        )
                    )
        logger.info("Exa ingestion collected %d articles", len(articles))
        return articles


def _parse_date(value) -> datetime | None:
    if not value:
        return None
    try:
        from dateutil import parser

        return parser.parse(value)
    except (ValueError, TypeError):
        return None
