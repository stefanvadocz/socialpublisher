"""Business logic over Suggestion rows: query, edit, approve, reject, publish."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.enums import Platform, PublishStatus, SuggestionStatus
from app.models import PublishAttempt, Suggestion
from app.pipeline.publish.factory import get_publisher

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def list_suggestions(
    db: Session, status: SuggestionStatus | None = None
) -> list[Suggestion]:
    stmt = select(Suggestion)
    if status is not None:
        stmt = stmt.where(Suggestion.status == status)
    stmt = stmt.order_by(Suggestion.rank_score.desc(), Suggestion.created_at.desc())
    return list(db.execute(stmt).scalars().unique())


def get_suggestion(db: Session, suggestion_id: int) -> Suggestion | None:
    return db.get(Suggestion, suggestion_id)


def status_counts(db: Session) -> dict[str, int]:
    counts: dict[str, int] = {}
    for suggestion in db.execute(select(Suggestion)).scalars().unique():
        status = suggestion.status
        key = status.value if isinstance(status, SuggestionStatus) else status
        counts[key] = counts.get(key, 0) + 1
    return counts


def update_caption(
    db: Session, suggestion: Suggestion, caption: str, hashtags: list[str] | None = None
) -> Suggestion:
    suggestion.edited_caption = caption
    if hashtags is not None:
        suggestion.hashtags = hashtags
    db.commit()
    db.refresh(suggestion)
    return suggestion


def select_image(db: Session, suggestion: Suggestion, image_id: int) -> Suggestion:
    found = False
    for img in suggestion.images:
        is_match = img.id == image_id
        img.is_selected = is_match
        found = found or is_match
    if found:
        suggestion.image_id = image_id
    db.commit()
    db.refresh(suggestion)
    return suggestion


def approve(db: Session, suggestion: Suggestion) -> Suggestion:
    suggestion.status = SuggestionStatus.APPROVED
    suggestion.reviewed_at = _utcnow()
    db.commit()
    db.refresh(suggestion)
    return suggestion


def reject(db: Session, suggestion: Suggestion) -> Suggestion:
    suggestion.status = SuggestionStatus.REJECTED
    suggestion.reviewed_at = _utcnow()
    db.commit()
    db.refresh(suggestion)
    return suggestion


def publish(
    db: Session, suggestion: Suggestion, settings: Settings | None = None
) -> Suggestion:
    """Publish via the configured publisher and record per-platform attempts."""
    settings = settings or get_settings()
    publisher = get_publisher(settings)

    image = suggestion.selected_image
    image_url = image.full_url if image else ""
    targets = suggestion.target_platforms or [Platform.FACEBOOK, Platform.INSTAGRAM]
    caption = suggestion.effective_caption
    if suggestion.hashtags:
        caption = caption + "\n\n" + " ".join(f"#{h}" for h in suggestion.hashtags)

    suggestion.status = SuggestionStatus.PUBLISHING
    db.commit()

    results = publisher.publish(caption=caption, image_url=image_url, targets=targets)

    all_ok = True
    last_post_id: str | None = None
    errors: list[str] = []
    for platform, result in results.items():
        db.add(
            PublishAttempt(
                suggestion_id=suggestion.id,
                platform=platform,
                status=PublishStatus.PUBLISHED if result.ok else PublishStatus.FAILED,
                external_post_id=result.external_post_id,
                error_message=result.error,
            )
        )
        if result.ok:
            last_post_id = result.external_post_id
        else:
            all_ok = False
            errors.append(f"{platform.value}: {result.error}")

    if all_ok:
        suggestion.status = SuggestionStatus.PUBLISHED
        suggestion.published_at = _utcnow()
        suggestion.external_post_id = last_post_id
        suggestion.error_message = None
    else:
        suggestion.status = SuggestionStatus.FAILED
        suggestion.error_message = "; ".join(errors)

    db.commit()
    db.refresh(suggestion)
    return suggestion
