"""
Global exception handlers for the FastAPI application.

Provides structured error responses for validation errors,
audio processing errors, and unhandled exceptions.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class AudioMasteringError(Exception):
    """Base exception for audio mastering errors."""

    def __init__(self, message: str, error_type: str = "audio_error"):
        self.message = message
        self.error_type = error_type
        super().__init__(message)


def register_error_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI application."""

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        logger.error("Validation error: %s", exc)
        return JSONResponse(
            status_code=422,
            content={
                "error_type": "validation_error",
                "message": "Request validation failed",
                "details": exc.errors(),
            },
        )

    @app.exception_handler(AudioMasteringError)
    async def audio_mastering_error_handler(request: Request, exc: AudioMasteringError):
        logger.error("Audio mastering error: %s", exc.message)
        return JSONResponse(
            status_code=400,
            content={
                "error_type": exc.error_type,
                "message": exc.message,
            },
        )

    @app.exception_handler(Exception)
    async def general_error_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content={
                "error_type": "internal_error",
                "message": "An unexpected error occurred",
            },
        )
