"""Application configuration via pydantic-settings.

All settings are read from environment variables / a local ``.env`` file. Every
external provider defaults to a mock (or keyless RSS) implementation so the app
runs end-to-end without any paid API keys.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# Built-in PR / communications news feeds used when RSS_FEEDS is left blank.
DEFAULT_RSS_FEEDS: list[str] = [
    "https://www.prnewswire.com/rss/news-releases-list.rss",
    "https://www.businesswire.com/portal/site/home/news/",
    "https://www.prweek.com/rss",
    "https://www.prdaily.com/feed/",
    "https://www.bulldogreporter.com/feed/",
    "https://feeds.feedburner.com/oreilly/radar",
]

# Keywords used by the ranking scorer to gauge PR relevance.
DEFAULT_PR_KEYWORDS: list[str] = [
    "public relations",
    "pr campaign",
    "communications",
    "media relations",
    "crisis communication",
    "brand reputation",
    "press release",
    "publicity",
    "spokesperson",
    "earned media",
    "thought leadership",
]

# Search queries used by web-search providers (firecrawl/exa).
DEFAULT_SEARCH_QUERIES: list[str] = [
    "public relations news",
    "PR campaign success",
    "crisis communications",
    "brand reputation management",
    "media relations trends",
]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Core
    app_env: str = "local"
    database_url: str = "sqlite:///./app.db"
    timezone: str = "America/Toronto"
    daily_run_hour: int = 7

    # Provider selection
    search_provider: str = "rss"  # rss | firecrawl | exa
    caption_provider: str = "mock"  # mock | claude
    image_provider: str = "mock"  # mock | unsplash | pexels
    publisher: str = "mock"  # mock | meta

    # AI captions
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-5"

    # Web search
    firecrawl_api_key: str = ""
    exa_api_key: str = ""
    rss_feeds: str = ""  # comma-separated; blank => DEFAULT_RSS_FEEDS

    # Stock images
    unsplash_access_key: str = ""
    pexels_api_key: str = ""

    # Meta publishing (later)
    meta_page_id: str = ""
    meta_page_access_token: str = ""
    meta_ig_user_id: str = ""
    meta_graph_version: str = "v21.0"

    # Ranking weights
    rank_w_authority: float = 0.45
    rank_w_pr_outlet: float = 0.15
    rank_w_recency: float = 0.20
    rank_w_keyword: float = 0.20
    max_daily_suggestions: int = 8
    max_article_age_hours: int = 72

    @property
    def feed_list(self) -> list[str]:
        if self.rss_feeds.strip():
            return [f.strip() for f in self.rss_feeds.split(",") if f.strip()]
        return DEFAULT_RSS_FEEDS

    @property
    def pr_keywords(self) -> list[str]:
        return DEFAULT_PR_KEYWORDS

    @property
    def search_queries(self) -> list[str]:
        return DEFAULT_SEARCH_QUERIES


@lru_cache
def get_settings() -> Settings:
    return Settings()
