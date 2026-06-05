"""Selects a caption generator from settings, falling back to the mock."""

from __future__ import annotations

import logging

from app.config import Settings
from app.pipeline.caption.base import CaptionGenerator
from app.pipeline.caption.mock import MockCaptionGenerator

logger = logging.getLogger(__name__)


def get_caption_generator(settings: Settings) -> CaptionGenerator:
    if settings.caption_provider.lower() == "claude":
        if settings.anthropic_api_key:
            from app.pipeline.caption.claude import ClaudeCaptionGenerator

            return ClaudeCaptionGenerator(settings.anthropic_api_key, settings.claude_model)
        logger.warning("CAPTION_PROVIDER=claude but ANTHROPIC_API_KEY missing; using mock")
    return MockCaptionGenerator()


def caption_model_name(settings: Settings) -> str:
    if settings.caption_provider.lower() == "claude" and settings.anthropic_api_key:
        return settings.claude_model
    return "mock"
