from datetime import datetime, timezone
from typing import Any

import redis.asyncio as redis
from redis.exceptions import RedisError

from app.core.config import REDIS_CONVERSATION_TTL_SECONDS, REDIS_URL
from app.core.logger import log_error, log_event
from app.core.rate_limiter import check_rate_limit
from app.services.conversation_service import get_conversation_state, save_conversation_state
from app.tools.memory_tool import append_memory, get_memory
from app.memory.memory_manager import MemoryManager
from app.models.memory_models import ConversationMemory, MemoryConfig
from app.models.message_models import ChatMessage, MessageRole
from app.models.session_models import SessionMetadata, SessionState

DEFAULT_HISTORY_LIMIT = 12

_redis_client: redis.Redis | None = None


class MemoryServiceError(RuntimeError):
    """Raised when the production memory facade cannot complete an operation."""


def _get_redis_client() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        if not REDIS_URL:
            raise MemoryServiceError("REDIS_URL is not configured")
        _redis_client = redis.from_url(
            REDIS_URL,
            decode_responses=True,
            health_check_interval=30,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
    return _redis_client


async def close_memory_service_client() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


def _workflow_key(user_id: str) -> str:
    return f"agent:workflow:{str(user_id).strip()}"


async def save_message(user_id: str, role: str, content: str, metadata: dict[str, Any] | None = None) -> list[Any]:
    """Append one UTF-8-safe message to Redis conversation memory."""
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **({"metadata": metadata} if metadata else {}),
    }
    history = await append_memory(user_id, message)
    log_event("memory_message_saved", user_id=user_id, role=role, history_count=len(history))
    return history


async def get_recent_history(user_id: str, limit: int = DEFAULT_HISTORY_LIMIT) -> list[Any]:
    """Return the most recent short-term memory turns for agent context."""
    history = await get_memory(user_id)
    return history[-max(1, int(limit)) :]


async def update_language(user_id: str, preferred_language: str, last_detected_language: str | None = None) -> dict[str, Any]:
    """Persist user language preference in the shared conversation state."""
    state = await get_conversation_state(user_id) or {"user_id": user_id}
    state["preferred_language"] = preferred_language
    state["last_detected_language"] = last_detected_language or preferred_language
    state["language_updated_at"] = datetime.now(timezone.utc).isoformat()
    saved = await save_conversation_state(state)
    log_event(
        "language_memory_updated",
        user_id=user_id,
        preferred_language=preferred_language,
        last_detected_language=state["last_detected_language"],
    )
    return saved


async def get_user_state(user_id: str) -> dict[str, Any]:
    """Combine conversation, workflow, and rate-limit state for agent planning."""
    conversation_state = await get_conversation_state(user_id) or {}
    workflow_state = {}
    try:
        raw_workflow = await _get_redis_client().hgetall(_workflow_key(user_id))
        workflow_state = dict(raw_workflow or {})
    except RedisError as exc:
        log_error("Workflow state read failed", user_id=user_id, error_type=type(exc).__name__)
    rate_limit = await check_rate_limit(user_id, scope="user", limit_type="message", increment=False)
    return {
        "conversation_state": conversation_state,
        "workflow_state": workflow_state,
        "rate_limit": rate_limit,
    }


async def update_workflow_state(user_id: str, values: dict[str, Any]) -> dict[str, Any]:
    """Store temporary workflow state such as pending meeting slot selection."""
    if not values:
        return {}
    serializable = {key: str(value) for key, value in values.items() if value is not None}
    try:
        client = _get_redis_client()
        await client.hset(_workflow_key(user_id), mapping=serializable)
        await client.expire(_workflow_key(user_id), REDIS_CONVERSATION_TTL_SECONDS)
    except RedisError as exc:
        log_error("Workflow state save failed", user_id=user_id, error_type=type(exc).__name__)
        raise MemoryServiceError("failed to save workflow state") from exc
    log_event("workflow_state_updated", user_id=user_id, keys=sorted(serializable))
    return serializable


class ShortTermMemoryService:
    """R6 Redis short-term memory facade for active AI conversations."""

    def __init__(self, *, memory_manager: MemoryManager | None = None, config: MemoryConfig | None = None) -> None:
        self.memory_manager = memory_manager or MemoryManager(config=config)

    async def create_session(self, user_id: str, metadata: SessionMetadata | None = None) -> SessionState:
        return await self.memory_manager.start_session(user_id, metadata)

    async def store_message(
        self,
        *,
        session_id: str,
        user_id: str,
        role: MessageRole,
        message_text: str,
        metadata: dict[str, Any] | None = None,
        message_id: str | None = None,
    ) -> ChatMessage:
        return await self.memory_manager.store_message(
            session_id=session_id,
            user_id=user_id,
            role=role,
            message_text=message_text,
            metadata=metadata,
            message_id=message_id,
        )

    async def get_active_context(self, session_id: str) -> ConversationMemory:
        return await self.memory_manager.get_conversation_memory(session_id)

    async def clear_session(self, session_id: str) -> bool:
        return await self.memory_manager.clear_session(session_id)
