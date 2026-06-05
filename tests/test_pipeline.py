"""End-to-end pipeline test using mock providers and an in-memory DB."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.config import Settings
from app.enums import SuggestionStatus
from app.models import Article, ImageCandidate, Suggestion
from app.pipeline import orchestrator
from app.pipeline.ingestion.base import RawArticle


class _FakeSearch:
    def __init__(self, articles):
        self._articles = articles

    def search(self, queries, limit):
        return self._articles


@pytest.fixture()
def patched_providers(monkeypatch):
    now = datetime.now(timezone.utc)
    articles = [
        RawArticle(
            url="https://prnewswire.com/story-1",
            title="PR agency wins award for communications campaign",
            snippet="A press release about media relations success.",
            published_at=now,
        ),
        RawArticle(
            url="https://prweek.com/story-2",
            title="Crisis communications trends for brand reputation",
            snippet="Communications leaders weigh in.",
            published_at=now,
        ),
    ]
    monkeypatch.setattr(
        orchestrator, "get_search_provider", lambda s: _FakeSearch(articles)
    )
    return articles


def test_run_daily_pipeline_creates_suggestions(db, patched_providers):
    settings = Settings(caption_provider="mock", image_provider="mock", search_provider="rss")
    summary = orchestrator.run_daily_pipeline(db, settings)

    assert summary.suggestions_created == 2
    assert summary.skipped_existing == 0

    suggestions = db.query(Suggestion).all()
    assert len(suggestions) == 2
    for s in suggestions:
        assert s.status == SuggestionStatus.SUGGESTED
        assert s.caption  # mock caption is non-empty
        assert s.images  # image candidates attached
        assert s.selected_image is not None  # first one auto-selected
        assert s.rank_score > 0


def test_pipeline_dedupes_on_rerun(db, patched_providers):
    settings = Settings(caption_provider="mock", image_provider="mock")
    orchestrator.run_daily_pipeline(db, settings)
    second = orchestrator.run_daily_pipeline(db, settings)

    assert second.suggestions_created == 0
    assert second.skipped_existing == 2
    assert db.query(Article).count() == 2
    assert db.query(ImageCandidate).count() > 0
