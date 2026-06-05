"""Pydantic DTOs for the JSON/ops API."""

from __future__ import annotations

from pydantic import BaseModel


class PipelineRunResponse(BaseModel):
    ingested: int
    ranked: int
    suggestions_created: int
    skipped_existing: int


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
