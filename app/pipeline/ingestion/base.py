"""Search-provider abstraction for the ingestion stage."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urlparse


@dataclass
class RawArticle:
    """A normalized article returned by any search provider."""

    url: str
    title: str
    snippet: str = ""
    domain: str = ""
    published_at: datetime | None = None
    raw_meta: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.domain and self.url:
            self.domain = domain_of(self.url)


def domain_of(url: str) -> str:
    """Extract a bare registrable-ish domain (drops a leading ``www.``)."""
    netloc = urlparse(url).netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc


class SearchProvider(ABC):
    """Discovers candidate articles for a set of queries."""

    @abstractmethod
    def search(self, queries: list[str], limit: int) -> list[RawArticle]:
        ...
