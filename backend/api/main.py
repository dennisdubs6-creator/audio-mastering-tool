from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from api.core.logging import setup_logging
from api.database import init_db
from api.routers import health, analyze, references


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    logger.info("Starting Audio Mastering Tool API")
    await init_db()
    logger.info("Database initialized")
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

app.include_router(health.router)
app.include_router(analyze.router)
app.include_router(references.router)
