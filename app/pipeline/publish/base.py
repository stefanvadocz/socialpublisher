"""Publisher abstraction shared by the mock and (future) Meta implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.enums import Platform


@dataclass
class PublishResult:
    ok: bool
    external_post_id: str | None = None
    error: str | None = None


class Publisher(ABC):
    @abstractmethod
    def publish(
        self, *, caption: str, image_url: str, targets: list[Platform]
    ) -> dict[Platform, PublishResult]:
        """Publish the post to each target platform; return a per-platform result."""
