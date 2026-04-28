"""Unit tests for app.infrastructure.logging — JSON formatter, dev formatter, setup."""

from __future__ import annotations

import json
import logging

from app.infrastructure.logging import (
    DevFormatter,
    JSONFormatter,
    request_id_ctx,
    setup_logging,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_record(
    msg: str = "hello",
    level: int = logging.INFO,
    name: str = "test",
) -> logging.LogRecord:
    return logging.LogRecord(
        name=name,
        level=level,
        pathname="test.py",
        lineno=1,
        msg=msg,
        args=(),
        exc_info=None,
    )


# ---------------------------------------------------------------------------
# JSONFormatter
# ---------------------------------------------------------------------------
class TestJSONFormatter:
    def test_output_is_valid_json(self) -> None:
        fmt = JSONFormatter()
        line = fmt.format(_make_record())
        parsed = json.loads(line)
        assert isinstance(parsed, dict)

    def test_contains_required_fields(self) -> None:
        fmt = JSONFormatter()
        parsed = json.loads(fmt.format(_make_record("test msg")))
        assert parsed["message"] == "test msg"
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test"
        assert "timestamp" in parsed
        assert "request_id" in parsed

    def test_includes_request_id_from_context(self) -> None:
        token = request_id_ctx.set("abc-123")
        try:
            fmt = JSONFormatter()
            parsed = json.loads(fmt.format(_make_record()))
            assert parsed["request_id"] == "abc-123"
        finally:
            request_id_ctx.reset(token)

    def test_request_id_is_none_when_unset(self) -> None:
        fmt = JSONFormatter()
        parsed = json.loads(fmt.format(_make_record()))
        assert parsed["request_id"] is None

    def test_includes_exception_info(self) -> None:
        fmt = JSONFormatter()
        try:
            raise ValueError("boom")
        except ValueError:
            import sys

            record = _make_record()
            record.exc_info = sys.exc_info()
            parsed = json.loads(fmt.format(record))
            assert "boom" in parsed["exception"]


# ---------------------------------------------------------------------------
# DevFormatter
# ---------------------------------------------------------------------------
class TestDevFormatter:
    def test_output_contains_message(self) -> None:
        fmt = DevFormatter()
        line = fmt.format(_make_record("dev message"))
        assert "dev message" in line

    def test_output_contains_level(self) -> None:
        fmt = DevFormatter()
        line = fmt.format(_make_record(level=logging.WARNING))
        assert "WARNING" in line

    def test_includes_short_request_id(self) -> None:
        token = request_id_ctx.set("abcdefgh-1234-5678")
        try:
            fmt = DevFormatter()
            line = fmt.format(_make_record())
            assert "[abcdefgh]" in line
        finally:
            request_id_ctx.reset(token)

    def test_no_request_id_bracket_when_unset(self) -> None:
        fmt = DevFormatter()
        line = fmt.format(_make_record())
        assert "[" not in line or "test" in line  # no rid bracket


# ---------------------------------------------------------------------------
# setup_logging
# ---------------------------------------------------------------------------
class TestSetupLogging:
    def _cleanup_root(self) -> None:
        root = logging.getLogger()
        root.handlers.clear()
        root.setLevel(logging.WARNING)

    def test_dev_sets_debug_level(self) -> None:
        self._cleanup_root()
        setup_logging(environment="development")
        root = logging.getLogger()
        assert root.level == logging.DEBUG
        assert len(root.handlers) == 1
        assert isinstance(root.handlers[0].formatter, DevFormatter)
        self._cleanup_root()

    def test_production_sets_info_level_and_json(self) -> None:
        self._cleanup_root()
        setup_logging(environment="production")
        root = logging.getLogger()
        assert root.level == logging.INFO
        assert isinstance(root.handlers[0].formatter, JSONFormatter)
        self._cleanup_root()

    def test_suppresses_noisy_loggers(self) -> None:
        self._cleanup_root()
        setup_logging(environment="production")
        assert logging.getLogger("pypsa").level == logging.WARNING
        assert logging.getLogger("linopy").level == logging.WARNING
        self._cleanup_root()
