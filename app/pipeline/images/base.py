"""Stock-image provider abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ImageCandidateDTO:
    provider: str
    external_id: str
    thumb_url: str
    full_url: str
    photographer: str = ""
    attribution: str = ""


class ImageProvider(ABC):
    @abstractmethod
    def search(self, query: str, count: int = 5) -> list[ImageCandidateDTO]:
        ...
