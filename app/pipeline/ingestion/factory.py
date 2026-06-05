"""Selects a search provider from settings, with a safe fallback to RSS."""

from __future__ import annotations

import logging

from app.config import Settings
from app.pipeline.ingestion.base import SearchProvider
from app.pipeline.ingestion.rss import RSSSearchProvider

logger = logging.getLogger(__name__)


def get_search_provider(settings: Settings) -> SearchProvider:
    choice = settings.search_provider.lower()

    if choice == "firecrawl":
        if settings.firecrawl_api_key:
            from app.pipeline.ingestion.firecrawl import FirecrawlSearchProvider

            return FirecrawlSearchProvider(settings.firecrawl_api_key)
        logger.warning("SEARCH_PROVIDER=firecrawl but FIRECRAWL_API_KEY missing; using RSS")

    elif choice == "exa":
        if settings.exa_api_key:
            from app.pipeline.ingestion.exa import ExaSearchProvider

            return ExaSearchProvider(settings.exa_api_key)
        logger.warning("SEARCH_PROVIDER=exa but EXA_API_KEY missing; using RSS")

    return RSSSearchProvider(settings.feed_list)
