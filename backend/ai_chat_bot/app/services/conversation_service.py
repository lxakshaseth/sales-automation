import json
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as redis
from redis.exceptions import RedisError

from app.core.config import REDIS_CONVERSATION_TTL_SECONDS, REDIS_URL
from app.core.event_bus import EVENT_CONVERSATION_CLOSED, EVENT_MESSAGE_RECEIVED, emit_event
from app.core.logger import log_error, log_event
from app.services.language_service import detect_language, should_switch_language
from app.tools.memory_tool import append_memory, get_memory

CONVERSATION_KEY_PREFIX = "agent:conversation"
ACTIVE_CONVERSATIONS_KEY = "agent:conversation:active"
STATUS_OPEN = "open"
STATUS_CLOSED = "closed"
DEFAULT_LANGUAGE = "en"
LANGUAGE_CONFIDENCE_THRESHOLD = 0.65

_redis_client: redis.Redis | None = None


class ConversationStateError(RuntimeError):
    """Raised when Redis conversation lifecycle state cannot be updated."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_now() -> str:
    return _utc_now().isoformat()


def _conversation_key(user_id: str) -> str:
    if not user_id or not str(user_id).strip():
        raise ValueError("user_id is required")
    return f"{CONVERSATION_KEY_PREFIX}:{str(user_id).strip()}"


def _get_redis_client() -> redis.Redis:
    """Reuse one Redis async client and its connection pool for state operations."""
    global _redis_client
    if _redis_client is None:
        if not REDIS_URL:
            raise ConversationStateError("REDIS_URL is not configured")
        _redis_client = redis.from_url(
            REDIS_URL,
            decode_responses=True,
            health_check_interval=30,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
    return _redis_client


async def close_conversation_client() -> None:
    """Close the Redis connection pool during FastAPI shutdown."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


def _deserialize_state(raw_value: str | bytes | None) -> dict[str, Any] | None:
    if raw_value is None:
        return None
    if isinstance(raw_value, bytes):
        raw_value = raw_value.decode("utf-8")
    try:
        state = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise ConversationStateError("stored conversation state is not valid JSON") from exc
    if not isinstance(state, dict):
        raise ConversationStateError("stored conversation state must be a JSON object")
    return state


async def get_conversation_state(user_id: str) -> dict[str, Any] | None:
    """Read one user's lifecycle state from Redis."""
    try:
        raw_value = await _get_redis_client().get(_conversation_key(user_id))
    except RedisError as exc:
        log_error("Conversation state read failed", user_id=user_id, error_type=type(exc).__name__)
        raise ConversationStateError("failed to read conversation state") from exc
    return _deserialize_state(raw_value)


async def save_conversation_state(state: dict[str, Any]) -> dict[str, Any]:
    """Persist lifecycle state with a TTL so stale conversations expire naturally."""
    user_id = str(state.get("user_id") or "").strip()
    if not user_id:
        raise ValueError("state.user_id is required")
    try:
        client = _get_redis_client()
        await client.set(
            _conversation_key(user_id),
            json.dumps(state, ensure_ascii=False, default=str),
            ex=REDIS_CONVERSATION_TTL_SECONDS,
        )
        if state.get("conversation_status") == STATUS_CLOSED:
            await client.srem(ACTIVE_CONVERSATIONS_KEY, user_id)
        else:
            await client.sadd(ACTIVE_CONVERSATIONS_KEY, user_id)
    except RedisError as exc:
        log_error("Conversation state save failed", user_id=user_id, error_type=type(exc).__name__)
        raise ConversationStateError("failed to save conversation state") from exc
    return state


async def list_active_conversation_ids() -> list[str]:
    """Return active user ids for scan-style scheduler checks and future analytics."""
    try:
        values = await _get_redis_client().smembers(ACTIVE_CONVERSATIONS_KEY)
    except RedisError as exc:
        log_error("Active conversation list failed", error_type=type(exc).__name__)
        raise ConversationStateError("failed to list active conversations") from exc
    return sorted(str(value) for value in values)


async def record_message_received(user_id: str, phone_number: str, message: str) -> dict[str, Any]:
    """
    Start or refresh a conversation when the user sends a message.

    This is the main lifecycle entrypoint: it updates timestamps, reopens closed
    chats, resets reminder state, appends short-term memory, and schedules the new
    inactivity reminder/auto-close jobs.
    """
    existing = await get_conversation_state(user_id)
    now = _iso_now()
    language_detection = detect_language(message)
    switch_request = should_switch_language(message)
    previous_language = (existing or {}).get("preferred_language") or DEFAULT_LANGUAGE

    if switch_request.get("should_switch"):
        preferred_language = switch_request["language_code"]
        language_confidence = switch_request["confidence"]
    elif not existing or not (existing or {}).get("preferred_language"):
        preferred_language = language_detection["language_code"] or DEFAULT_LANGUAGE
        language_confidence = language_detection["confidence"]
    elif language_detection["confidence"] >= LANGUAGE_CONFIDENCE_THRESHOLD:
        preferred_language = language_detection["language_code"]
        language_confidence = language_detection["confidence"]
    else:
        preferred_language = previous_language
        language_confidence = (existing or {}).get("language_confidence", 0.0)

    state = {
        "user_id": user_id,
        "phone_number": phone_number,
        "last_message_time": now,
        "reminder_sent": False,
        "conversation_status": STATUS_OPEN,
        "conversation_start_time": (existing or {}).get("conversation_start_time") or now,
        "conversation_end_time": None,
        "preferred_language": preferred_language,
        "language_confidence": language_confidence,
        "last_detected_language": language_detection["language_code"],
        "last_language_detected": language_detection["language_code"],
        "last_language_confidence": language_detection["confidence"],
    }
    if switch_request.get("should_switch"):
        state["language_switch_requested"] = True
        state["language_switch_confirmation"] = switch_request["confirmation_message"]

    await save_conversation_state(state)
    await append_memory(user_id, {"role": "user", "content": message, "timestamp": now})

    from app.scheduler.reminder_scheduler import schedule_inactivity_reminder
    from app.scheduler.close_chat_scheduler import schedule_auto_close

    await schedule_inactivity_reminder(user_id)
    await schedule_auto_close(user_id)

    log_event(
        "message_received",
        user_id=user_id,
        phone_number=phone_number,
        preferred_language=preferred_language,
        language_confidence=language_confidence,
        last_language_detected=language_detection["language_code"],
    )
    if switch_request.get("should_switch"):
        log_event(
            "language_switch",
            user_id=user_id,
            previous_language=previous_language,
            preferred_language=preferred_language,
            confidence=language_confidence,
        )
    await emit_event(EVENT_MESSAGE_RECEIVED, {"user_id": user_id, "phone_number": phone_number}, handle_local=True)
    return state


async def record_assistant_message(user_id: str, message: str) -> list[Any]:
    """Store the assistant reply in Redis memory for future summary and context."""
    return await append_memory(user_id, {"role": "assistant", "content": message, "timestamp": _iso_now()})


def inactive_minutes(state: dict[str, Any], now: datetime | None = None) -> float:
    """Calculate inactivity duration from last user message."""
    now = now or _utc_now()
    last_message_time = datetime.fromisoformat(str(state["last_message_time"]).replace("Z", "+00:00"))
    if last_message_time.tzinfo is None:
        last_message_time = last_message_time.replace(tzinfo=timezone.utc)
    return (now - last_message_time.astimezone(timezone.utc)).total_seconds() / 60


async def mark_reminder_sent(user_id: str) -> dict[str, Any]:
    """Set reminder_sent=true after the autonomous reminder message is delivered."""
    state = await get_conversation_state(user_id)
    if not state:
        raise ConversationStateError("conversation state not found")
    state["reminder_sent"] = True
    return await save_conversation_state(state)


async def close_conversation(user_id: str, summary: dict[str, Any] | None = None) -> dict[str, Any]:
    """Mark a conversation closed and remove it from the active conversation set."""
    state = await get_conversation_state(user_id)
    if not state:
        raise ConversationStateError("conversation state not found")
    state["conversation_status"] = STATUS_CLOSED
    state["conversation_end_time"] = _iso_now()
    if summary is not None:
        state["summary"] = summary
    await save_conversation_state(state)
    log_event("conversation_closed", user_id=user_id, phone_number=state.get("phone_number"))
    await emit_event(EVENT_CONVERSATION_CLOSED, {"user_id": user_id, "summary": summary or {}}, handle_local=True)
    return state


async def get_conversation_history(user_id: str) -> list[Any]:
    """Return Redis JSON-list memory for summary generation and future CRM sync."""
    return await get_memory(user_id)
