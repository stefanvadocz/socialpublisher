"""Caption-generator abstraction and per-platform formatting helpers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.enums import Platform
from app.pipeline.ingestion.base import RawArticle

# Platform caption/hashtag guidelines applied after generation.
PLATFORM_LIMITS: dict[Platform, dict] = {
    Platform.INSTAGRAM: {"max_chars": 2200, "max_hashtags": 8},
    Platform.FACEBOOK: {"max_chars": 600, "max_hashtags": 2},
}


@dataclass
class CaptionResult:
    caption: str
    hashtags: list[str] = field(default_factory=list)
    image_query: str = ""


def apply_platform_limits(result: CaptionResult, platform: Platform) -> CaptionResult:
    """Truncate caption and trim hashtag count to platform guidelines."""
    limits = PLATFORM_LIMITS.get(platform, {"max_chars": 2200, "max_hashtags": 8})
    caption = result.caption.strip()
    if len(caption) > limits["max_chars"]:
        caption = caption[: limits["max_chars"] - 1].rstrip() + "…"
    hashtags = [h.lstrip("#") for h in result.hashtags if h.strip()][: limits["max_hashtags"]]
    return CaptionResult(caption=caption, hashtags=hashtags, image_query=result.image_query)


class CaptionGenerator(ABC):
    @abstractmethod
    def generate(self, article: RawArticle, platform: Platform) -> CaptionResult:
        ...
