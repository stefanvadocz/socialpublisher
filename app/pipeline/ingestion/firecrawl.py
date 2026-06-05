"""Firecrawl web-search provider (optional, requires FIRECRAWL_API_KEY).

Calls the Firecrawl search REST API via httpx. Enabled with
``SEARCH_PROVIDER=firecrawl``.
"""

from __future__ import annotations

import logging
from datetime import datetime

import httpx

from app.pipeline.ingestion.base import RawArticle, SearchProvider

logger = logging.getLogger(__name__)

FIRECRAWL_SEARCH_URL = "https://api.firecrawl.dev/v1/search"


class FirecrawlSearchProvider(SearchProvider):
    def __init__(self, api_key: str, timeout: float = 30.0):
        self.api_key = api_key
        self.timeout = timeout

    def search(self, queries: list[str], limit: int) -> list[RawArticle]:
        articles: list[RawArticle] = []
        seen: set[str] = set()
        per_query = max(1, limit // max(1, len(queries)))
        headers = {"Authorization": f"Bearer {self.api_key}"}

        with httpx.Client(timeout=self.timeout) as client:
            for query in queries:
                try:
                    resp = client.post(
                        FIRECRAWL_SEARCH_URL,
                        headers=headers,
                        json={"query": query, "limit": per_query, "sources": ["news", "web"]},
                    )
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as exc:
                    logger.warning("Firecrawl search failed for %r: %s", query, exc)
                    continue

                for item in _iter_results(data):
                    url = (item.get("url") or "").strip()
                    title = (item.get("title") or "").strip()
                    if not url or not title or url in seen:
                        continue
                    seen.add(url)
                    articles.append(
                        RawArticle(
                            url=url,
                            title=title,
                            snippet=(item.get("description") or item.get("snippet") or "")[:500],
                            published_at=_parse_date(item.get("publishedDate") or item.get("date")),
                            raw_meta={"query": query, "provider": "firecrawl"},
                        )
                    )
        logger.info("Firecrawl ingestion collected %d articles", len(articles))
        return articles


def _iter_results(data: dict):
    payload = data.get("data", data)
    if isinstance(payload, dict):
        for key in ("news", "web", "results"):
            if isinstance(payload.get(key), list):
                yield from payload[key]
    elif isinstance(payload, list):
        yield from payload


def _parse_date(value) -> datetime | None:
    if not value:
        return None
    try:
        from dateutil import parser

        return parser.parse(value)
    except (ValueError, TypeError):
        return None
