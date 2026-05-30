import json
import logging
import os
import sys
import time
from collections.abc import Callable
from contextvars import ContextVar
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from typing import Any
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import LOG_BACKUP_COUNT, LOG_FILE_PATH, LOG_LEVEL, LOG_MAX_BYTES, LOG_STRUCTURED

request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)

LOGGER_NAME = "ai_chat_bot"
_configured = False


class RequestIdFilter(logging.Filter):
    """Inject the current async request id into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_context.get() or "-"
        return True


class StructuredFormatter(logging.Formatter):
    """Format logs as JSON for ingestion by production log pipelines."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
            "event_type": getattr(record, "event_type", "log"),
        }

        extra = getattr(record, "structured_extra", None)
        if isinstance(extra, dict):
            payload.update(extra)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False, default=str)


class HumanFormatter(logging.Formatter):
    """Readable console/file format for local development."""

    def format(self, record: logging.LogRecord) -> str:
        record.event_type = getattr(record, "event_type", "log")
        return super().format(record)


def _make_formatter() -> logging.Formatter:
    if LOG_STRUCTURED:
        return StructuredFormatter()

    return HumanFormatter(
        "[%(levelname)s] %(asctime)s request_id=%(request_id)s event=%(event_type)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )


def configure_logging() -> logging.Logger:
    """
    Configure root logging once.

    Existing module loggers from tools, queue, scheduler, and agent components will
    propagate into these handlers automatically.
    """
    global _configured

    logger = logging.getLogger(LOGGER_NAME)
    if _configured:
        return logger

    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    request_filter = RequestIdFilter()
    formatter = _make_formatter()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.addFilter(request_filter)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    log_dir = os.path.dirname(LOG_FILE_PATH)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    file_handler = RotatingFileHandler(
        LOG_FILE_PATH,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.addFilter(request_filter)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    logger.setLevel(level)
    logger.propagate = True
    _configured = True
    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a configured logger for app modules."""
    configure_logging()
    return logging.getLogger(name or LOGGER_NAME)


def set_request_id(request_id: str | None = None):
    """Set request id for the current async context and return the reset token."""
    return request_id_context.set(request_id or str(uuid4()))


def get_request_id() -> str | None:
    return request_id_context.get()


def reset_request_id(token) -> None:
    request_id_context.reset(token)


def _log(level: int, message: str, event_type: str, **metadata: Any) -> None:
    logger = get_logger()
    logger.log(
        level,
        message,
        extra={
            "event_type": event_type,
            "structured_extra": metadata,
        },
    )


def log_info(message: str, **metadata: Any) -> None:
    """Log general backend information."""
    _log(logging.INFO, message, "info", **metadata)


def log_error(message: str, **metadata: Any) -> None:
    """Log errors from tools, APIs, queue workers, or autonomous tasks."""
    exc_info = metadata.pop("exc_info", None)
    logger = get_logger()
    logger.error(
        message,
        exc_info=exc_info,
        extra={
            "event_type": "error",
            "structured_extra": metadata,
        },
    )


def log_action(action: str, **metadata: Any) -> None:
    """Log AI/tool actions such as create_lead, send_email, or book_meeting."""
    _log(logging.INFO, f"{action} executed", "action", action=action, **metadata)


def log_event(event: str, **metadata: Any) -> None:
    """Log domain events such as appointment_booked or queue_recovered."""
    _log(logging.INFO, event, "event", event=event, **metadata)


class LoggingMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware that logs request lifecycle with request IDs."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid4())
        token = set_request_id(request_id)
        started_at = time.perf_counter()

        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            log_event(
                "http_request",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
            )
            response.headers["x-request-id"] = request_id
            return response
        except Exception as exc:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            log_error(
                "Unhandled request error",
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
                exc_info=True,
                error_type=type(exc).__name__,
            )
            raise
        finally:
            reset_request_id(token)
