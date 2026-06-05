"""Anthropic Claude caption generator."""

from __future__ import annotations

import json
import logging
import re

from app.enums import Platform
from app.pipeline.caption.base import (
    CaptionGenerator,
    CaptionResult,
    apply_platform_limits,
)
from app.pipeline.caption.mock import MockCaptionGenerator
from app.pipeline.caption.prompts import SYSTEM_PROMPT, build_user_prompt
from app.pipeline.ingestion.base import RawArticle

logger = logging.getLogger(__name__)


class ClaudeCaptionGenerator(CaptionGenerator):
    def __init__(self, api_key: str, model: str):
        # Imported lazily so the dependency is only needed when enabled.
        import anthropic

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self._fallback = MockCaptionGenerator()

    def generate(self, article: RawArticle, platform: Platform) -> CaptionResult:
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=0.7,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": build_user_prompt(article, platform)}],
            )
            text = "".join(
                block.text for block in message.content if block.type == "text"
            )
            data = _extract_json(text)
            result = CaptionResult(
                caption=str(data.get("caption", "")).strip(),
                hashtags=[str(h) for h in data.get("hashtags", [])],
                image_query=str(data.get("image_query", "")).strip(),
            )
            if not result.caption:
                raise ValueError("empty caption from model")
            return apply_platform_limits(result, platform)
        except Exception as exc:
            logger.warning("Claude caption failed (%s); falling back to mock", exc)
            return self._fallback.generate(article, platform)


def _extract_json(text: str) -> dict:
    """Parse JSON from the model output, tolerating prose or code fences."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise
