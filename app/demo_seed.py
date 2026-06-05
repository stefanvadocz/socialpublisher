"""Demo data seeding shared by the CLI seed script and optional seed-on-start.

``seed_if_empty`` is safe to call on every boot — it only inserts sample posts
when the suggestions table is empty, so deployments come up with something to
look at without wiping real data on restart.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums import Platform, SuggestionStatus
from app.models import Article, ImageCandidate, Source, Suggestion
from app.pipeline.images.mock import MockImageProvider

SAMPLES = [
    {
        "domain": "prnewswire.com",
        "title": "Global Brand Launches AI-Powered Newsroom to Modernize Media Relations",
        "snippet": "The new platform helps communications teams pitch journalists with "
        "data-driven story angles and real-time coverage analytics.",
        "score": 0.91,
        "caption": "📣 Big shift in media relations: a major brand just launched an "
        "AI-powered newsroom to help PR teams pitch smarter and track coverage in "
        "real time. The future of earned media is data-driven. 🚀",
        "hashtags": ["PublicRelations", "MediaRelations", "PRtech", "Communications"],
    },
    {
        "domain": "prweek.com",
        "title": "Crisis Communications in 2026: Why Speed and Transparency Win",
        "snippet": "Industry leaders share lessons from recent high-profile crises and "
        "the playbooks that protected brand reputation.",
        "score": 0.84,
        "caption": "When a crisis hits, speed and transparency beat spin every time. "
        "Here are the communications playbooks protecting brand reputation in 2026. 🛡️",
        "hashtags": ["CrisisComms", "Reputation", "PR"],
    },
    {
        "domain": "forbes.com",
        "title": "Thought Leadership Is the New Advertising — Here's How Executives Get It Right",
        "snippet": "Executives who publish authentic, useful insights are outperforming "
        "traditional paid campaigns on trust and engagement.",
        "score": 0.72,
        "caption": "Thought leadership is the new advertising. Executives sharing "
        "authentic, useful insights are winning on trust — no ad budget required. ✍️",
        "hashtags": ["ThoughtLeadership", "ExecComms", "ContentMarketing"],
    },
]


def insert_samples(db: Session) -> int:
    """Insert the demo suggestions; returns the number created."""
    images = MockImageProvider()
    for i, sample in enumerate(SAMPLES):
        source = db.execute(
            select(Source).where(Source.domain == sample["domain"])
        ).scalar_one_or_none()
        if source is None:
            source = Source(
                domain=sample["domain"],
                name=sample["domain"],
                authority_score=sample["score"],
                is_pr_outlet="pr" in sample["domain"],
            )
            db.add(source)
            db.flush()

        article = Article(
            source_id=source.id,
            url=f"https://{sample['domain']}/sample-article-{i}",
            title=sample["title"],
            snippet=sample["snippet"],
            published_at=datetime.now(timezone.utc) - timedelta(hours=4 * i + 2),
            domain=sample["domain"],
            relevance_score=sample["score"],
            raw_meta={"seed": True},
        )
        db.add(article)
        db.flush()

        suggestion = Suggestion(
            article_id=article.id,
            status=SuggestionStatus.SUGGESTED,
            targets=[Platform.FACEBOOK.value, Platform.INSTAGRAM.value],
            caption=sample["caption"],
            hashtags=sample["hashtags"],
            rank_score=sample["score"],
            ai_model="mock",
        )
        db.add(suggestion)
        db.flush()

        for idx, img in enumerate(images.search(sample["title"], count=4)):
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
    db.commit()
    return len(SAMPLES)


def seed_if_empty(db: Session) -> int:
    """Insert demo data only when there are no suggestions yet."""
    existing = db.execute(select(Suggestion.id).limit(1)).first()
    if existing is not None:
        return 0
    return insert_samples(db)


def reseed(db: Session) -> int:
    """Clear suggestions/articles and re-insert the demo data (for local dev)."""
    db.query(ImageCandidate).delete()
    db.query(Suggestion).delete()
    db.query(Article).delete()
    db.commit()
    return insert_samples(db)
