"""Structured logging configuration."""
from __future__ import annotations

import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from ai_content_radar.config.settings import DATA_DIR, config


class StructuredFormatter(logging.Formatter):
    """Formats log records as structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if hasattr(record, "duration"):
            log_data["duration_ms"] = record.duration

        if hasattr(record, "api_call"):
            log_data["api_call"] = record.api_call

        if hasattr(record, "search_query"):
            log_data["search_query"] = record.search_query

        if record.exc_info and record.exc_info[0]:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, default=str)


class PerformanceFilter(logging.Filter):
    """Filter that adds performance context to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        return True


class Timer:
    """Context manager for timing operations."""

    def __init__(self, operation: str, logger: logging.Logger):
        self.operation = operation
        self.logger = logger
        self.start_time = 0.0
        self.duration = 0.0

    def __enter__(self) -> Timer:
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.duration = (time.time() - self.start_time) * 1000
        extra = {"duration": self.duration}
        if exc_type:
            self.logger.error(
                f"{self.operation} failed after {self.duration:.1f}ms",
                extra=extra,
                exc_info=True,
            )
        else:
            self.logger.info(
                f"{self.operation} completed in {self.duration:.1f}ms",
                extra=extra,
            )


def setup_logging() -> logging.Logger:
    """Configure structured logging for the application."""
    log_dir = DATA_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "content_radar.log"

    root_logger = logging.getLogger("ai_content_radar")
    root_logger.setLevel(getattr(logging, config.log.level.upper(), logging.INFO))

    if root_logger.handlers:
        return root_logger

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = StructuredFormatter()
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(file_handler)

    root_logger.info("Logging initialized", extra={"log_file": str(log_file)})
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a named logger."""
    return logging.getLogger(f"ai_content_radar.{name}")
