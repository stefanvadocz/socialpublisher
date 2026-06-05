"""Seed the database with sample sources and suggestions for local development.

Run: ``python scripts/seed.py``  (safe to re-run; it clears prior seed rows).
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Allow running as a plain script (`python scripts/seed.py`).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import SessionLocal, init_db  # noqa: E402
from app.enums import Platform, SuggestionStatus  # noqa: E402
from app.models import Article, ImageCandidate, Source, Suggestion  # noqa: E402
from app.pipeline.images.mock import MockImageProvider  # noqa: E402

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


def main() -> None:
    init_db()
    db = SessionLocal()
    images = MockImageProvider()
    try:
        # Clear any previous seed data so the script is idempotent.
        db.query(ImageCandidate).delete()
        db.query(Suggestion).delete()
        db.query(Article).delete()
        db.commit()

        for i, sample in enumerate(SAMPLES):
            source = (
                db.query(Source).filter(Source.domain == sample["domain"]).one_or_none()
            )
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
        print(f"Seeded {len(SAMPLES)} suggestions. Run: uvicorn app.main:app --reload")
    finally:
        db.close()


if __name__ == "__main__":
    main()
