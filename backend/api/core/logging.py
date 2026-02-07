"""
Logging configuration using the Python standard ``logging`` module.

Sets up dual handlers (console + rotating file) at application startup.
Call ``setup_logging()`` once during the FastAPI lifespan.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from api.core.config import settings

_CONSOLE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_FILE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s"
_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
_BACKUP_COUNT = 5


def setup_logging() -> None:
    """Configure the root logger with console and file handlers.

    - **Console**: ``StreamHandler`` with a concise format.
    - **File**: ``RotatingFileHandler`` writing to ``settings.LOG_FILE``,
      rotating at 10 MB with 5 backups.

    The log level is controlled by ``settings.LOG_LEVEL`` (default INFO).
    """
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Only add console handler if no handlers exist yet (avoids duplicates
    # when uvicorn has already configured console logging).
    if not root_logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(logging.Formatter(_CONSOLE_FORMAT))
        root_logger.addHandler(console_handler)

    # Always add the file handler – skip only if one is already attached
    # (e.g. from a repeated setup_logging() call).
    if any(isinstance(h, RotatingFileHandler) for h in root_logger.handlers):
        return

    # File handler
    log_file = Path(settings.LOG_FILE).expanduser()
    log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        str(log_file),
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(_FILE_FORMAT))
    root_logger.addHandler(file_handler)

    logging.getLogger(__name__).info(
        "Logging configured at level %s – file: %s", settings.LOG_LEVEL, log_file
    )
