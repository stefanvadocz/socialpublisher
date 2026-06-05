"""APScheduler wiring for the daily morning pipeline run."""

from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import get_settings
from app.db import SessionLocal
from app.pipeline.orchestrator import run_daily_pipeline

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _run_pipeline_job() -> None:
    """Job entrypoint — owns its own DB session."""
    settings = get_settings()
    db = SessionLocal()
    try:
        summary = run_daily_pipeline(db, settings)
        logger.info("Scheduled daily pipeline finished: %s", summary.as_dict())
    except Exception:
        logger.exception("Scheduled daily pipeline failed")
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    settings = get_settings()
    scheduler = BackgroundScheduler(timezone=settings.timezone)
    scheduler.add_job(
        _run_pipeline_job,
        trigger=CronTrigger(hour=settings.daily_run_hour, minute=0),
        id="daily_pipeline",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "Scheduler started: daily pipeline at %02d:00 %s",
        settings.daily_run_hour, settings.timezone,
    )
    _scheduler = scheduler
    return scheduler


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
