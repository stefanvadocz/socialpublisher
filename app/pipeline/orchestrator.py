"""Daily pipeline: ingest -> rank -> caption + image -> persist suggestions."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.enums import Platform, SuggestionStatus
from app.models import Article, ImageCandidate, Source, Suggestion
from app.pipeline.caption.base import CaptionResult
from app.pipeline.caption.factory import caption_model_name, get_caption_generator
from app.pipeline.images.factory import get_image_provider
from app.pipeline.ingestion.base import RawArticle
from app.pipeline.ingestion.factory import get_search_provider
from app.pipeline.ranking.authority import lookup
from app.pipeline.ranking.scorer import ScoreBreakdown, rank_articles

logger = logging.getLogger(__name__)

# Default platforms each suggested post targets.
DEFAULT_TARGETS = [Platform.FACEBOOK, Platform.INSTAGRAM]


@dataclass
class PipelineSummary:
    ingested: int
    ranked: int
    suggestions_created: int
    skipped_existing: int

    def as_dict(self) -> dict:
        return {
            "ingested": self.ingested,
            "ranked": self.ranked,
            "suggestions_created": self.suggestions_created,
            "skipped_existing": self.skipped_existing,
        }


def _get_or_create_source(db: Session, domain: str) -> Source:
    source = db.execute(select(Source).where(Source.domain == domain)).scalar_one_or_none()
    if source is None:
        authority, is_pr = lookup(domain)
        source = Source(
            domain=domain, name=domain, authority_score=authority, is_pr_outlet=is_pr
        )
        db.add(source)
        db.flush()
    return source


def _persist_article(
    db: Session, raw: RawArticle, score: ScoreBreakdown
) -> Article | None:
    """Insert an Article if its URL is new; return None if it already exists."""
    existing = db.execute(select(Article).where(Article.url == raw.url)).scalar_one_or_none()
    if existing is not None:
        return None
    source = _get_or_create_source(db, raw.domain)
    article = Article(
        source_id=source.id,
        url=raw.url,
        title=raw.title,
        snippet=raw.snippet,
        published_at=raw.published_at,
        domain=raw.domain,
        relevance_score=score.total,
        raw_meta=raw.raw_meta,
    )
    db.add(article)
    db.flush()
    return article


def _build_suggestion(
    db: Session,
    article: Article,
    raw: RawArticle,
    caption: CaptionResult,
    images,
    model_name: str,
) -> Suggestion:
    suggestion = Suggestion(
        article_id=article.id,
        status=SuggestionStatus.SUGGESTED,
        targets=[p.value for p in DEFAULT_TARGETS],
        caption=caption.caption,
        hashtags=caption.hashtags,
        rank_score=article.relevance_score,
        ai_model=model_name,
    )
    db.add(suggestion)
    db.flush()

    for idx, img in enumerate(images):
        db.add(
            ImageCandidate(
                suggestion_id=suggestion.id,
                provider=img.provider,
                external_id=img.external_id,
                thumb_url=img.thumb_url,
                full_url=img.full_url,
                photographer=img.photographer,
                attribution=img.attribution,
                is_selected=(idx == 0),
            )
        )
    db.flush()
    return suggestion


def run_daily_pipeline(db: Session, settings: Settings | None = None) -> PipelineSummary:
    """Run the full discovery -> suggestion pipeline once."""
    settings = settings or get_settings()

    search = get_search_provider(settings)
    caption_gen = get_caption_generator(settings)
    image_provider = get_image_provider(settings)
    model_name = caption_model_name(settings)

    fetch_limit = settings.max_daily_suggestions
    raw_articles = search.search(settings.search_queries, limit=fetch_limit)
    logger.info("Ingested %d raw articles", len(raw_articles))

    ranked = rank_articles(raw_articles, settings)
    top = ranked[: settings.max_daily_suggestions]

    created = 0
    skipped = 0
    # Caption uses the first target platform as the formatting baseline.
    baseline_platform = DEFAULT_TARGETS[0]

    for raw, score in top:
        article = _persist_article(db, raw, score)
        if article is None:
            skipped += 1
            continue
        caption = caption_gen.generate(raw, baseline_platform)
        query = caption.image_query or raw.title
        images = image_provider.search(query, count=5)
        _build_suggestion(db, article, raw, caption, images, model_name)
        created += 1

    db.commit()
    summary = PipelineSummary(
        ingested=len(raw_articles),
        ranked=len(ranked),
        suggestions_created=created,
        skipped_existing=skipped,
    )
    logger.info("Pipeline summary: %s", summary.as_dict())
    return summary
