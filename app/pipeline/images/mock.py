"""Placeholder image provider (keyless) using picsum.photos."""

from __future__ import annotations

import hashlib

from app.pipeline.images.base import ImageCandidateDTO, ImageProvider


class MockImageProvider(ImageProvider):
    def search(self, query: str, count: int = 5) -> list[ImageCandidateDTO]:
        candidates: list[ImageCandidateDTO] = []
        for i in range(count):
            seed = hashlib.md5(f"{query}-{i}".encode()).hexdigest()[:10]
            candidates.append(
                ImageCandidateDTO(
                    provider="mock",
                    external_id=seed,
                    thumb_url=f"https://picsum.photos/seed/{seed}/320/200",
                    full_url=f"https://picsum.photos/seed/{seed}/1080/1080",
                    photographer="Lorem Picsum",
                    attribution="Placeholder image via picsum.photos",
                )
            )
        return candidates
