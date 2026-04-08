"""Logging configuration for the Cikkiro application."""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict

from src.core.constants import LOG_FORMAT


class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


def get_logger(
    name: str,
    level: int = logging.INFO,
    use_json: bool = True,
) -> logging.Logger:
    """
    Get or create a logger instance.

    Args:
        name: Logger name (typically __name__)
        level: Logging level (default: INFO)
        use_json: Whether to use JSON formatting (default: True)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    # Set formatter
    if use_json:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(LOG_FORMAT)

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    **context: Any,
) -> None:
    """
    Log message with additional context fields.

    Args:
        logger: Logger instance
        level: Logging level
        message: Log message
        **context: Additional context fields to log
    """
    # Create a log record with extra fields
    record = logger.makeRecord(
        logger.name,
        level,
        "(unknown file)",
        0,
        message,
        (),
        None,
    )

    if context:
        record.extra_fields = context

    logger.handle(record)
