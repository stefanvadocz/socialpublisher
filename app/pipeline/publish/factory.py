"""Selects a publisher from settings, defaulting to the mock."""

from __future__ import annotations

import logging

from app.config import Settings
from app.pipeline.publish.base import Publisher
from app.pipeline.publish.mock import MockPublisher

logger = logging.getLogger(__name__)


def get_publisher(settings: Settings) -> Publisher:
    if settings.publisher.lower() == "meta":
        from app.pipeline.publish.meta import MetaPublisher

        return MetaPublisher(settings)
    return MockPublisher()
