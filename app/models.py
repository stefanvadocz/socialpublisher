"""SQLAlchemy ORM models.

The schema separates raw ingested ``Article`` rows from the ``Suggestion`` rows
that make up the review queue, so re-ranking and dedupe stay simple. Image
candidates and publish attempts hang off a suggestion for swapping and auditing.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.enums import Platform, PublishStatus, SuggestionStatus


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    domain: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    authority_score: Mapped[float] = mapped_column(Float, default=0.3)
    is_pr_outlet: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"), nullable=True)
    url: Mapped[str] = mapped_column(String(1024), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(512))
    snippet: Mapped[str] = mapped_column(Text, default="")
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    domain: Mapped[str] = mapped_column(String(255), index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    raw_meta: Mapped[dict] = mapped_column(JSON, default=dict)

    source: Mapped[Source | None] = relationship("Source", lazy="joined")
    suggestion: Mapped["Suggestion | None"] = relationship(
        "Suggestion", back_populates="article", uselist=False
    )


class Suggestion(Base):
    __tablename__ = "suggestions"

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"))
    status: Mapped[SuggestionStatus] = mapped_column(
        String(20), default=SuggestionStatus.SUGGESTED, index=True
    )
    # Target platforms for this post, e.g. ["facebook", "instagram"].
    targets: Mapped[list] = mapped_column(JSON, default=list)
    caption: Mapped[str] = mapped_column(Text, default="")
    hashtags: Mapped[list] = mapped_column(JSON, default=list)
    edited_caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    # use_alter avoids a circular-FK cycle with image_candidates.suggestion_id.
    image_id: Mapped[int | None] = mapped_column(
        ForeignKey("image_candidates.id", use_alter=True, name="fk_suggestion_image"),
        nullable=True,
    )
    rank_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    ai_model: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    external_post_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    article: Mapped[Article] = relationship(
        "Article", back_populates="suggestion", lazy="joined"
    )
    images: Mapped[list["ImageCandidate"]] = relationship(
        "ImageCandidate",
        back_populates="suggestion",
        cascade="all, delete-orphan",
        foreign_keys="ImageCandidate.suggestion_id",
    )
    attempts: Mapped[list["PublishAttempt"]] = relationship(
        "PublishAttempt", back_populates="suggestion", cascade="all, delete-orphan"
    )

    @property
    def effective_caption(self) -> str:
        """User edit wins over the AI-generated caption."""
        return self.edited_caption if self.edited_caption else self.caption

    @property
    def selected_image(self) -> "ImageCandidate | None":
        for img in self.images:
            if img.is_selected:
                return img
        return self.images[0] if self.images else None

    @property
    def target_platforms(self) -> list[Platform]:
        return [Platform(t) for t in (self.targets or [])]


class ImageCandidate(Base):
    __tablename__ = "image_candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    suggestion_id: Mapped[int] = mapped_column(ForeignKey("suggestions.id"))
    provider: Mapped[str] = mapped_column(String(32), default="mock")
    external_id: Mapped[str] = mapped_column(String(255), default="")
    thumb_url: Mapped[str] = mapped_column(String(1024), default="")
    full_url: Mapped[str] = mapped_column(String(1024), default="")
    photographer: Mapped[str] = mapped_column(String(255), default="")
    attribution: Mapped[str] = mapped_column(String(512), default="")
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False)

    suggestion: Mapped[Suggestion] = relationship(
        "Suggestion", back_populates="images", foreign_keys=[suggestion_id]
    )


class PublishAttempt(Base):
    __tablename__ = "publish_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    suggestion_id: Mapped[int] = mapped_column(ForeignKey("suggestions.id"))
    platform: Mapped[Platform] = mapped_column(String(20))
    status: Mapped[PublishStatus] = mapped_column(String(20))
    external_post_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    suggestion: Mapped[Suggestion] = relationship(
        "Suggestion", back_populates="attempts"
    )
