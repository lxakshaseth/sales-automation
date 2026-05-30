import asyncio
import inspect
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import redis.asyncio as redis
from redis.exceptions import RedisError

from app.core.config import REDIS_OPERATION_TIMEOUT_SECONDS, REDIS_URL
from app.core.logger import get_request_id, log_error, log_event
from app.core.retry_handler import RetryConfig, retry_async

EVENT_MESSAGE_RECEIVED = "message_received"
EVENT_REMINDER_SENT = "reminder_sent"
EVENT_CONVERSATION_CLOSED = "conversation_closed"
EVENT_SUMMARY_GENERATED = "summary_generated"
EVENT_EMAIL_SENT = "email_sent"
EVENT_LEAD_SAVED = "lead_saved"
EVENT_APPOINTMENT_BOOKED = "appointment_booked"
EVENT_FOLLOWUP_TRIGGERED = "followup_triggered"
EVENT_TOOL_FAILED = "tool_failed"

DEFAULT_EVENT_CHANNEL = "agent:events"
DEFAULT_HANDLER_TIMEOUT_SECONDS = 15.0

EventHandler = Callable[[dict[str, Any]], Awaitable[Any] | Any]

_handlers: dict[str, list[EventHandler]] = {}
_redis_client: redis.Redis | None = None


@dataclass(frozen=True)
class Event:
    """Structured event envelope for autonomous AI workflow modules."""

    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "name": self.name,
            "payload": self.payload,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


class EventBusError(RuntimeError):
    """Raised when event emission or handling fails."""


def _get_redis_client() -> redis.Redis:
    """Reuse a single async Redis client for event publishing."""
    global _redis_client

    if _redis_client is None:
        if not REDIS_URL:
            raise EventBusError("REDIS_URL is not configured")

        _redis_client = redis.from_url(
            REDIS_URL,
            decode_responses=True,
            health_check_interval=30,
            socket_connect_timeout=REDIS_OPERATION_TIMEOUT_SECONDS,
            socket_timeout=REDIS_OPERATION_TIMEOUT_SECONDS,
            retry_on_timeout=True,
        )

    return _redis_client


async def close_event_bus() -> None:
    """Close Redis resources during FastAPI shutdown or tests."""
    global _redis_client

    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


def _normalize_event(
    event_name: str,
    payload: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> Event:
    if not event_name or not event_name.strip():
        raise ValueError("event_name is required")

    return Event(
        name=event_name.strip(),
        payload=payload or {},
        metadata={
            "request_id": get_request_id(),
            **(metadata or {}),
        },
    )


def subscribe_event(event_name: str, handler: EventHandler) -> EventHandler:
    """
    Register an event handler.

    Handlers may be async or sync. Multiple modules can subscribe to the same event,
    allowing message memory, lead tracking, scheduler, and analytics to react
    independently.
    """
    if not event_name or not event_name.strip():
        raise ValueError("event_name is required")

    if not callable(handler):
        raise TypeError("handler must be callable")

    _handlers.setdefault(event_name.strip(), []).append(handler)
    return handler


async def _run_handler(handler: EventHandler, event: dict[str, Any]) -> Any:
    result = handler(event)
    if inspect.isawaitable(result):
        return await result
    return result


async def handle_event(
    event: dict[str, Any] | Event,
    *,
    retry_config: RetryConfig | None = None,
) -> list[dict[str, Any]]:
    """Execute all local subscribers for an event with retry and timeout protection."""
    event_dict = event.to_dict() if isinstance(event, Event) else event
    event_name = event_dict.get("name")
    handlers = list(_handlers.get(event_name, []))
    results: list[dict[str, Any]] = []

    log_event("event_handling_started", event_name=event_name, event_id=event_dict.get("event_id"), handler_count=len(handlers))

    for handler in handlers:
        handler_name = getattr(handler, "__name__", handler.__class__.__name__)

        @retry_async(
            config=retry_config
            or RetryConfig(max_attempts=3, base_delay_seconds=0.25, max_delay_seconds=5, timeout_seconds=DEFAULT_HANDLER_TIMEOUT_SECONDS),
        )
        async def _protected_handler(handler: EventHandler = handler) -> Any:
            return await asyncio.wait_for(_run_handler(handler, event_dict), timeout=DEFAULT_HANDLER_TIMEOUT_SECONDS)

        try:
            handler_result = await _protected_handler()
            results.append({"handler": handler_name, "success": True, "result": handler_result})
            log_event("event_handler_completed", event_name=event_name, event_id=event_dict.get("event_id"), handler=handler_name)
        except Exception as exc:
            results.append({"handler": handler_name, "success": False, "error": str(exc), "error_type": type(exc).__name__})
            log_error(
                "Event handler failed",
                event_name=event_name,
                event_id=event_dict.get("event_id"),
                handler=handler_name,
                error_type=type(exc).__name__,
            )

    return results


async def _publish_to_redis(event: Event, channel: str) -> None:
    try:
        await asyncio.wait_for(
            _get_redis_client().publish(channel, json.dumps(event.to_dict(), ensure_ascii=False)),
            timeout=REDIS_OPERATION_TIMEOUT_SECONDS,
        )
    except (TimeoutError, RedisError) as exc:
        log_error("Redis event publish failed", event_name=event.name, event_id=event.event_id, error_type=type(exc).__name__)
        raise EventBusError("failed to publish event to Redis") from exc


async def emit_event(
    event_name: str,
    payload: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    *,
    publish_redis: bool = False,
    handle_local: bool = True,
    channel: str = DEFAULT_EVENT_CHANNEL,
) -> dict[str, Any]:
    """
    Emit an event to local subscribers and optionally Redis pub/sub.

    This lets the current process react immediately while leaving a path for
    cross-worker consumers as the AI system grows.
    """
    event = _normalize_event(event_name, payload, metadata)
    log_event("event_emitted", event_name=event.name, event_id=event.event_id, metadata=event.metadata)

    redis_published = False
    if publish_redis:
        await _publish_to_redis(event, channel)
        redis_published = True

    handler_results = await handle_event(event) if handle_local else []
    return {
        "success": True,
        "event": event.to_dict(),
        "redis_published": redis_published,
        "handler_results": handler_results,
    }


async def default_logging_handler(event: dict[str, Any]) -> dict[str, Any]:
    """Default subscriber that records every event for observability."""
    log_event(
        event.get("name", "unknown_event"),
        event_id=event.get("event_id"),
        payload=event.get("payload", {}),
        metadata=event.get("metadata", {}),
    )
    return {"logged": True}


for _event_name in [
    EVENT_MESSAGE_RECEIVED,
    EVENT_REMINDER_SENT,
    EVENT_CONVERSATION_CLOSED,
    EVENT_SUMMARY_GENERATED,
    EVENT_EMAIL_SENT,
    EVENT_LEAD_SAVED,
    EVENT_APPOINTMENT_BOOKED,
    EVENT_FOLLOWUP_TRIGGERED,
    EVENT_TOOL_FAILED,
]:
    subscribe_event(_event_name, default_logging_handler)
