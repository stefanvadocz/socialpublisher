"""Selects a stock-image provider from settings, falling back to the mock."""

from __future__ import annotations

import logging

from app.config import Settings
from app.pipeline.images.base import ImageProvider
from app.pipeline.images.mock import MockImageProvider

logger = logging.getLogger(__name__)


def get_image_provider(settings: Settings) -> ImageProvider:
    choice = settings.image_provider.lower()

    if choice == "unsplash":
        if settings.unsplash_access_key:
            from app.pipeline.images.unsplash import UnsplashImageProvider

            return UnsplashImageProvider(settings.unsplash_access_key)
        logger.warning("IMAGE_PROVIDER=unsplash but UNSPLASH_ACCESS_KEY missing; using mock")

    elif choice == "pexels":
        if settings.pexels_api_key:
            from app.pipeline.images.pexels import PexelsImageProvider

            return PexelsImageProvider(settings.pexels_api_key)
        logger.warning("IMAGE_PROVIDER=pexels but PEXELS_API_KEY missing; using mock")

    return MockImageProvider()
