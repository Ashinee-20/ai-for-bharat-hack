"""Logging utilities for structured logging across all services."""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields if present
        if hasattr(record, "userId"):
            log_data["userId"] = record.userId
        if hasattr(record, "requestId"):
            log_data["requestId"] = record.requestId
        if hasattr(record, "metadata"):
            log_data["metadata"] = record.metadata

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging(level: str = "INFO") -> None:
    """Configure logging for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add structured JSON handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name.
    
    Args:
        name: Logger name (typically module name)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that adds context to all log messages."""

    def process(
        self, msg: str, kwargs: Dict[str, Any]
    ) -> tuple[str, Dict[str, Any]]:
        """Add extra context to log messages."""
        extra = kwargs.get("extra", {})
        extra.update(self.extra)
        kwargs["extra"] = extra
        return msg, kwargs
