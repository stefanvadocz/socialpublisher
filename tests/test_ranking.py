"""Tests for the ranking scorer and authority lookup."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.config import get_settings
from app.pipeline.ingestion.base import RawArticle, domain_of
from app.pipeline.ranking.authority import lookup
from app.pipeline.ranking.scorer import rank_articles, score_article


def test_domain_of_strips_www():
    assert domain_of("https://www.prnewswire.com/news/x") == "prnewswire.com"
    assert domain_of("https://blog.cision.com/post") == "blog.cision.com"


def test_authority_lookup_known_and_unknown():
    score, is_pr = lookup("prnewswire.com")
    assert score > 0.9 and is_pr is True
    score, is_pr = lookup("some-random-blog.example")
    assert score == 0.3 and is_pr is False


def test_authority_subdomain_inherits_parent():
    score, is_pr = lookup("newsroom.cision.com")
    assert score == lookup("cision.com")[0]


def test_high_authority_recent_pr_outranks_unknown_old():
    settings = get_settings()
    now = datetime.now(timezone.utc)
    strong = RawArticle(
        url="https://prnewswire.com/a",
        title="New public relations campaign drives media relations results",
        snippet="press release about communications",
        published_at=now,
    )
    weak = RawArticle(
        url="https://random-blog.example/b",
        title="My cat photos",
        snippet="nothing relevant here",
        published_at=now - timedelta(hours=40),
    )
    s_strong = score_article(strong, settings)
    s_weak = score_article(weak, settings)
    assert s_strong.total > s_weak.total
    assert 0.0 <= s_strong.total <= 1.0


def test_rank_articles_drops_stale_items():
    settings = get_settings()
    now = datetime.now(timezone.utc)
    fresh = RawArticle(url="https://prweek.com/fresh", title="PR news", published_at=now)
    stale = RawArticle(
        url="https://prweek.com/stale",
        title="Old PR news",
        published_at=now - timedelta(hours=settings.max_article_age_hours + 10),
    )
    ranked = rank_articles([fresh, stale], settings)
    urls = [a.url for a, _ in ranked]
    assert "https://prweek.com/fresh" in urls
    assert "https://prweek.com/stale" not in urls
