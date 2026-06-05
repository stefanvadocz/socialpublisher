"""Operational / JSON routes: health check and manual pipeline trigger."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import __version__
from app.db import get_db
from app.pipeline.orchestrator import run_daily_pipeline
from app.schemas import HealthResponse, PipelineRunResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(version=__version__)


@router.post("/jobs/run-daily", response_model=PipelineRunResponse)
def run_daily(db: Session = Depends(get_db)):
    """Manually trigger the daily discovery/suggestion pipeline."""
    summary = run_daily_pipeline(db)
    return PipelineRunResponse(**summary.as_dict())
