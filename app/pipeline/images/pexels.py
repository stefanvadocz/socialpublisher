"""Pexels stock-image provider (requires PEXELS_API_KEY)."""

from __future__ import annotations

import logging

import httpx

from app.pipeline.images.base import ImageCandidateDTO, ImageProvider

logger = logging.getLogger(__name__)

PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"


class PexelsImageProvider(ImageProvider):
    def __init__(self, api_key: str, timeout: float = 20.0):
        self.api_key = api_key
        self.timeout = timeout

    def search(self, query: str, count: int = 5) -> list[ImageCandidateDTO]:
        params = {"query": query or "public relations", "per_page": count}
        headers = {"Authorization": self.api_key}
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(PEXELS_SEARCH_URL, params=params, headers=headers)
                resp.raise_for_status()
                photos = resp.json().get("photos", [])
        except Exception as exc:
            logger.warning("Pexels search failed for %r: %s", query, exc)
            return []

        candidates: list[ImageCandidateDTO] = []
        for item in photos:
            name = item.get("photographer", "Unknown")
            src = item.get("src", {})
            candidates.append(
                ImageCandidateDTO(
                    provider="pexels",
                    external_id=str(item.get("id", "")),
                    thumb_url=src.get("medium", ""),
                    full_url=src.get("large", ""),
                    photographer=name,
                    attribution=f"Photo by {name} on Pexels",
                )
            )
        return candidates
