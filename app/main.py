"""FastAPI application factory and lifespan wiring."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.config import get_settings
from app.db import init_db
from app.services.scheduler import shutdown_scheduler, start_scheduler
from app.web.routes_api import router as api_router
from app.web.routes_dashboard import router as dashboard_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    logger.info("PR Social Publisher %s started", __version__)
    try:
        yield
    finally:
        shutdown_scheduler()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="PR Social Publisher", version=__version__, lifespan=lifespan)

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    app.include_router(api_router)
    app.include_router(dashboard_router)

    logger.info(
        "Providers: search=%s caption=%s image=%s publisher=%s",
        settings.search_provider, settings.caption_provider,
        settings.image_provider, settings.publisher,
    )
    return app


app = create_app()
