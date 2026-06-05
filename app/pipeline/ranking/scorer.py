"""Weighted relevance scoring for ingested articles.

score = w_authority * authority
      + w_pr_outlet * pr_outlet_bonus
      + w_recency   * recency
      + w_keyword   * keyword_relevance

All component signals are normalized to 0..1; with default weights summing to
1.0 the final score is also bounded to 0..1.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.config import Settings
from app.pipeline.ingestion.base import RawArticle
from app.pipeline.ranking.authority import lookup


@dataclass
class ScoreBreakdown:
    authority: float
    pr_outlet: float
    recency: float
    keyword: float
    total: float


def _recency_score(published_at: datetime | None) -> float:
    """Exponential decay: full weight today, halving every 24h."""
    if published_at is None:
        return 0.4  # unknown date => neutral-ish
    now = datetime.now(timezone.utc)
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
    age_hours = max(0.0, (now - published_at).total_seconds() / 3600.0)
    return 0.5 ** (age_hours / 24.0)


def _keyword_score(article: RawArticle, keywords: list[str]) -> float:
    """Normalized PR-keyword hits; title matches weigh double."""
    title = article.title.lower()
    body = article.snippet.lower()
    hits = 0.0
    for kw in keywords:
        kw = kw.lower()
        if kw in title:
            hits += 2.0
        elif kw in body:
            hits += 1.0
    return min(hits / 4.0, 1.0)


def score_article(article: RawArticle, settings: Settings) -> ScoreBreakdown:
    authority, is_pr_outlet = lookup(article.domain)
    pr_outlet = 1.0 if is_pr_outlet else 0.0
    recency = _recency_score(article.published_at)
    keyword = _keyword_score(article, settings.pr_keywords)

    total = (
        settings.rank_w_authority * authority
        + settings.rank_w_pr_outlet * pr_outlet
        + settings.rank_w_recency * recency
        + settings.rank_w_keyword * keyword
    )
    return ScoreBreakdown(
        authority=authority,
        pr_outlet=pr_outlet,
        recency=recency,
        keyword=keyword,
        total=round(total, 4),
    )


def rank_articles(
    articles: list[RawArticle], settings: Settings
) -> list[tuple[RawArticle, ScoreBreakdown]]:
    """Score, drop stale items, and sort by total score descending."""
    max_age = settings.max_article_age_hours
    now = datetime.now(timezone.utc)
    scored: list[tuple[RawArticle, ScoreBreakdown]] = []

    for article in articles:
        published = article.published_at
        if published is not None:
            if published.tzinfo is None:
                published = published.replace(tzinfo=timezone.utc)
            age_hours = (now - published).total_seconds() / 3600.0
            if age_hours > max_age:
                continue
        scored.append((article, score_article(article, settings)))

    scored.sort(key=lambda pair: pair[1].total, reverse=True)
    return scored
