"""RSS-based search provider (default, keyless).

Pulls recent items from a configured list of PR / communications news feeds.
``queries`` are ignored — feeds are the source of truth — but kept in the
signature to satisfy the :class:`SearchProvider` contract.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import feedparser

from app.pipeline.ingestion.base import RawArticle, SearchProvider

logger = logging.getLogger(__name__)


def _parse_published(entry) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        value = getattr(entry, key, None) or entry.get(key)
        if value:
            try:
                return datetime(*value[:6], tzinfo=timezone.utc)
            except (TypeError, ValueError):
                continue
    return None


def _clean(text: str) -> str:
    # Feeds often embed HTML in summaries; strip tags crudely for a snippet.
    import re

    text = re.sub(r"<[^>]+>", " ", text or "")
    return " ".join(text.split())[:500]


class RSSSearchProvider(SearchProvider):
    def __init__(self, feeds: list[str]):
        self.feeds = feeds

    def search(self, queries: list[str], limit: int) -> list[RawArticle]:
        articles: list[RawArticle] = []
        seen: set[str] = set()
        per_feed = max(1, limit // max(1, len(self.feeds)) + 2)

        for feed_url in self.feeds:
            try:
                parsed = feedparser.parse(feed_url)
            except Exception as exc:  # network / parse errors shouldn't kill the run
                logger.warning("Failed to parse feed %s: %s", feed_url, exc)
                continue

            for entry in parsed.entries[:per_feed]:
                url = entry.get("link", "").strip()
                title = entry.get("title", "").strip()
                if not url or not title or url in seen:
                    continue
                seen.add(url)
                snippet = _clean(entry.get("summary", "") or entry.get("description", ""))
                articles.append(
                    RawArticle(
                        url=url,
                        title=title,
                        snippet=snippet,
                        published_at=_parse_published(entry),
                        raw_meta={"feed": feed_url},
                    )
                )

        logger.info("RSS ingestion collected %d articles", len(articles))
        return articles[: limit * 3] if limit else articles
