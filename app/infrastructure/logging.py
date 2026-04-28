"""Structured logging setup for the PowerShift backend.

- **Production** (ENVIRONMENT != "development"): JSON-formatted log lines with
  request_id correlation, suitable for log aggregators.
- **Development**: human-readable colored output for local debugging.

Noisy third-party loggers (PyPSA, linopy, urllib3) are suppressed to WARNING.
"""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import ClassVar

# ---------------------------------------------------------------------------
# Context variable — set per-request by the middleware in main.py
# ---------------------------------------------------------------------------
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)

# ---------------------------------------------------------------------------
# Noisy loggers to suppress
# ---------------------------------------------------------------------------
_NOISY_LOGGERS: list[str] = [
    "pypsa",
    "linopy",
    "urllib3",
    "httpcore",
    "httpx",
    "uvicorn.access",
]


# ---------------------------------------------------------------------------
# JSON formatter — one JSON object per line
# ---------------------------------------------------------------------------
class JSONFormatter(logging.Formatter):
    """Emits each log record as a single JSON line with request_id."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_ctx.get(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            log_entry["stack_info"] = record.stack_info
        return json.dumps(log_entry, default=str)


# ---------------------------------------------------------------------------
# Colored dev formatter
# ---------------------------------------------------------------------------
class DevFormatter(logging.Formatter):
    """Human-readable formatter with ANSI colors and request_id."""

    _COLORS: ClassVar[dict[int, str]] = {
        logging.DEBUG: "\033[36m",     # cyan
        logging.INFO: "\033[32m",      # green
        logging.WARNING: "\033[33m",   # yellow
        logging.ERROR: "\033[31m",     # red
        logging.CRITICAL: "\033[1;31m",  # bold red
    }
    _RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self._COLORS.get(record.levelno, "")
        rid = request_id_ctx.get()
        rid_part = f" [{rid[:8]}]" if rid else ""
        base = f"{color}{record.levelname:<8}{self._RESET} {record.name}{rid_part} | {record.getMessage()}"
        if record.exc_info and record.exc_info[0] is not None:
            base += "\n" + self.formatException(record.exc_info)
        return base


# ---------------------------------------------------------------------------
# Public setup function — call once at startup
# ---------------------------------------------------------------------------
def setup_logging(*, environment: str = "development") -> None:
    """Configure the root logger for the given environment.

    Parameters
    ----------
    environment:
        ``"development"`` uses colored human-readable output at DEBUG level.
        Any other value uses JSON output at INFO level.
    """
    is_dev = environment.lower() == "development"
    level = logging.DEBUG if is_dev else logging.INFO

    root = logging.getLogger()
    # Remove any pre-existing handlers (e.g. from basicConfig)
    root.handlers.clear()
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if is_dev:
        handler.setFormatter(DevFormatter())
    else:
        handler.setFormatter(JSONFormatter())

    root.addHandler(handler)

    # Suppress noisy third-party loggers
    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
