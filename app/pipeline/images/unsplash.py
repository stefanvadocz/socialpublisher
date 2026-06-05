"""Unsplash stock-image provider (requires UNSPLASH_ACCESS_KEY).

Attribution is stored per Unsplash API guidelines (credit the photographer and
Unsplash).
"""

from __future__ import annotations

import logging

import httpx

from app.pipeline.images.base import ImageCandidateDTO, ImageProvider

logger = logging.getLogger(__name__)

UNSPLASH_SEARCH_URL = "https://api.unsplash.com/search/photos"


class UnsplashImageProvider(ImageProvider):
    def __init__(self, access_key: str, timeout: float = 20.0):
        self.access_key = access_key
        self.timeout = timeout

    def search(self, query: str, count: int = 5) -> list[ImageCandidateDTO]:
        params = {"query": query or "public relations", "per_page": count, "orientation": "squarish"}
        headers = {"Authorization": f"Client-ID {self.access_key}"}
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(UNSPLASH_SEARCH_URL, params=params, headers=headers)
                resp.raise_for_status()
                results = resp.json().get("results", [])
        except Exception as exc:
            logger.warning("Unsplash search failed for %r: %s", query, exc)
            return []

        candidates: list[ImageCandidateDTO] = []
        for item in results:
            user = item.get("user", {})
            name = user.get("name", "Unknown")
            candidates.append(
                ImageCandidateDTO(
                    provider="unsplash",
                    external_id=item.get("id", ""),
                    thumb_url=item.get("urls", {}).get("small", ""),
                    full_url=item.get("urls", {}).get("regular", ""),
                    photographer=name,
                    attribution=f"Photo by {name} on Unsplash",
                )
            )
        return candidates
