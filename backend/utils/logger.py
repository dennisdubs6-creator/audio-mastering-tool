"""
Convenience wrapper for the standard ``logging`` module.

Usage::

    from utils.logger import get_logger

    logger = get_logger(__name__)
    logger.info("Processing file %s", file_name)
"""

import logging


def get_logger(name: str) -> logging.Logger:
    """Return a logger for the given module name.

    Args:
        name: Typically ``__name__`` of the calling module.

    Returns:
        A configured ``logging.Logger`` instance.
    """
    return logging.getLogger(name)
