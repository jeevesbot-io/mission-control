"""Structured JSON logging configuration."""

import logging
import sys

from pythonjsonlogger.json import JsonFormatter

from core.config import settings


def setup_logging() -> None:
    """Configure structured JSON logging for production, standard for debug."""
    root = logging.getLogger()

    # Clear existing handlers
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if settings.debug:
        # Human-readable format for development
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )
        root.setLevel(logging.DEBUG)
    else:
        # Structured JSON for production
        handler.setFormatter(
            JsonFormatter(
                fmt="%(timestamp)s %(level)s %(name)s %(message)s",
                rename_fields={"levelname": "level", "asctime": "timestamp"},
                timestamp=True,
            )
        )
        root.setLevel(logging.INFO)

    root.addHandler(handler)

    # Quiet noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
