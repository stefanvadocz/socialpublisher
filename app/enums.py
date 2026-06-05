"""Enumerations shared across models, services, and templates."""

from __future__ import annotations

from enum import Enum


class SuggestionStatus(str, Enum):
    """Lifecycle of a suggested post.

    DISCOVERED -> SUGGESTED -> APPROVED -> (SCHEDULED) -> PUBLISHING -> PUBLISHED
    with side transitions to REJECTED and FAILED (retryable).
    """

    DISCOVERED = "discovered"
    SUGGESTED = "suggested"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    REJECTED = "rejected"
    FAILED = "failed"


class Platform(str, Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"


class PublishStatus(str, Enum):
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
