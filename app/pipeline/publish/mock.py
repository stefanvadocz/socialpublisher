"""Mock publisher — the MVP default. Logs the payload, returns fake post IDs."""

from __future__ import annotations

import logging
import uuid

from app.enums import Platform
from app.pipeline.publish.base import Publisher, PublishResult

logger = logging.getLogger(__name__)


class MockPublisher(Publisher):
    def publish(
        self, *, caption: str, image_url: str, targets: list[Platform]
    ) -> dict[Platform, PublishResult]:
        results: dict[Platform, PublishResult] = {}
        for platform in targets:
            fake_id = f"mock_{platform.value}_{uuid.uuid4().hex[:12]}"
            logger.info(
                "[MockPublisher] %s post=%s image=%s caption=%r",
                platform.value, fake_id, image_url, caption[:80],
            )
            results[platform] = PublishResult(ok=True, external_post_id=fake_id)
        return results
