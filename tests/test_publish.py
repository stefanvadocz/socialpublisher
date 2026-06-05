"""Tests for publish status transitions via the mock publisher."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.config import Settings
from app.enums import Platform, PublishStatus, SuggestionStatus
from app.models import Article, ImageCandidate, Source, Suggestion
from app.services import suggestions as svc


@pytest.fixture()
def suggestion(db) -> Suggestion:
    source = Source(domain="prweek.com", name="PRWeek", authority_score=0.9, is_pr_outlet=True)
    db.add(source)
    db.flush()
    article = Article(
        source_id=source.id,
        url="https://prweek.com/a",
        title="A PR story",
        domain="prweek.com",
        published_at=datetime.now(timezone.utc),
        relevance_score=0.8,
    )
    db.add(article)
    db.flush()
    s = Suggestion(
        article_id=article.id,
        status=SuggestionStatus.SUGGESTED,
        targets=[Platform.FACEBOOK.value, Platform.INSTAGRAM.value],
        caption="Hello PR world",
        hashtags=["PR"],
        rank_score=0.8,
        ai_model="mock",
    )
    db.add(s)
    db.flush()
    db.add(
        ImageCandidate(
            suggestion_id=s.id, provider="mock", external_id="x",
            thumb_url="t", full_url="https://example.com/full.jpg", is_selected=True,
        )
    )
    db.commit()
    db.refresh(s)
    return s


def test_approve_then_publish_marks_published(db, suggestion):
    settings = Settings(publisher="mock")
    svc.approve(db, suggestion)
    assert suggestion.status == SuggestionStatus.APPROVED
    assert suggestion.reviewed_at is not None

    svc.publish(db, suggestion, settings)
    assert suggestion.status == SuggestionStatus.PUBLISHED
    assert suggestion.published_at is not None
    assert suggestion.external_post_id

    attempts = suggestion.attempts
    assert len(attempts) == 2
    assert all(a.status == PublishStatus.PUBLISHED for a in attempts)


def test_edit_caption_overrides_effective_caption(db, suggestion):
    svc.update_caption(db, suggestion, "Edited text", ["NewTag"])
    assert suggestion.effective_caption == "Edited text"
    assert suggestion.hashtags == ["NewTag"]


def test_reject_sets_status(db, suggestion):
    svc.reject(db, suggestion)
    assert suggestion.status == SuggestionStatus.REJECTED


def test_select_image_switches_selection(db, suggestion):
    extra = ImageCandidate(
        suggestion_id=suggestion.id, provider="mock", external_id="y",
        thumb_url="t2", full_url="f2", is_selected=False,
    )
    db.add(extra)
    db.commit()
    db.refresh(suggestion)

    svc.select_image(db, suggestion, extra.id)
    assert suggestion.selected_image.id == extra.id
    assert suggestion.image_id == extra.id
