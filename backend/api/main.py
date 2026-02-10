"""
FastAPI application entry point.

Creates the app instance, configures CORS middleware, and wires up the
lifespan event to initialise the database and logging on startup.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.core.logging import setup_logging
from api.database import init_db
from api.error_handlers import register_error_handlers
from api.routers import health, analyze, progress, references, comparison
from api.routers.analyze import set_main_loop


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: setup on enter, teardown on exit."""
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Audio Mastering Tool API")
    init_db()
    logger.info("Database initialized")
    set_main_loop(asyncio.get_running_loop())
    yield
    logger.info("Shutting down Audio Mastering Tool API")


app = FastAPI(
    title="Audio Mastering Tool API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)

app.include_router(health.router)
app.include_router(analyze.router)
app.include_router(progress.router)
app.include_router(references.router)
app.include_router(comparison.router)
