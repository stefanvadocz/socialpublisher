"""Deterministic caption generator for keyless runs and tests."""

from __future__ import annotations

import re

from app.enums import Platform
from app.pipeline.caption.base import (
    CaptionGenerator,
    CaptionResult,
    apply_platform_limits,
)
from app.pipeline.ingestion.base import RawArticle

_STOPWORDS = {
    "the", "a", "an", "and", "or", "for", "to", "of", "in", "on", "with",
    "how", "why", "what", "as", "at", "by", "is", "are", "from",
}


def _keywords(text: str, n: int) -> list[str]:
    words = re.findall(r"[A-Za-z]{4,}", text.lower())
    seen: list[str] = []
    for w in words:
        if w not in _STOPWORDS and w not in seen:
            seen.append(w)
        if len(seen) >= n:
            break
    return seen


class MockCaptionGenerator(CaptionGenerator):
    def generate(self, article: RawArticle, platform: Platform) -> CaptionResult:
        kws = _keywords(article.title, 4)
        hashtags = [w.capitalize() for w in kws] + ["PR", "Communications"]
        caption = (
            f"📣 {article.title}\n\n"
            f"Worth a read for anyone in PR and communications. "
            f"Source: {article.domain}."
        )
        result = CaptionResult(
            caption=caption,
            hashtags=hashtags,
            image_query=" ".join(kws[:3]) or "public relations",
        )
        return apply_platform_limits(result, platform)
