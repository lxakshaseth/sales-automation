from redis.exceptions import RedisError

from app.core.logger import log_error, log_event
from app.exceptions.memory_exceptions import DuplicateMessageError, InvalidSessionError
from app.models.memory_models import MemoryConfig
from app.models.message_models import ChatMessage
from app.models.session_models import SessionState
from app.utils.redis_helpers import get_redis_memory_client, redis_error_to_memory_error
from app.utils.serialization_helpers import json_to_model, model_to_json


class RedisMemoryStore:
    """Redis-backed store for active short-term conversation memory."""

    def __init__(self, config: MemoryConfig | None = None) -> None:
        self.config = config or MemoryConfig()

    def session_key(self, session_id: str) -> str:
        return f"{self.config.redis_key_prefix}:session:{session_id}:state"

    def messages_key(self, session_id: str) -> str:
        return f"{self.config.redis_key_prefix}:session:{session_id}:messages"

    def user_sessions_key(self, user_id: str) -> str:
        return f"{self.config.redis_key_prefix}:user:{user_id}:sessions"

    async def store_session(self, session: SessionState) -> SessionState:
        try:
            client = get_redis_memory_client()
            await client.set(self.session_key(session.session_id), model_to_json(session), ex=self.config.session_ttl_seconds)
            await client.sadd(self.user_sessions_key(session.user_id), session.session_id)
            await client.expire(self.user_sessions_key(session.user_id), self.config.session_ttl_seconds)
            log_event("short_term_session_stored", session_id=session.session_id, user_id=session.user_id)
            return session
        except RedisError as exc:
            log_error("Redis session store failed", session_id=session.session_id, error_type=type(exc).__name__)
            raise redis_error_to_memory_error(exc) from exc

    async def fetch_session(self, session_id: str) -> SessionState | None:
        try:
            raw = await get_redis_memory_client().get(self.session_key(session_id))
            return json_to_model(raw, SessionState)
        except RedisError as exc:
            raise redis_error_to_memory_error(exc) from exc

    async def store_message(self, message: ChatMessage) -> ChatMessage:
        await self._ensure_session(message.session_id)
        try:
            client = get_redis_memory_client()
            recent_raw = await client.lrange(self.messages_key(message.session_id), -self.config.duplicate_check_limit, -1)
            for raw in recent_raw:
                existing = json_to_model(raw, ChatMessage)
                if existing and existing.message_id == message.message_id:
                    raise DuplicateMessageError("duplicate message id", details={"message_id": message.message_id})

            await client.rpush(self.messages_key(message.session_id), model_to_json(message))
            await client.expire(self.messages_key(message.session_id), self.config.session_ttl_seconds)
            await client.expire(self.session_key(message.session_id), self.config.session_ttl_seconds)
            log_event("short_term_message_stored", session_id=message.session_id, user_id=message.user_id, role=message.role)
            return message
        except DuplicateMessageError:
            raise
        except RedisError as exc:
            log_error("Redis message store failed", session_id=message.session_id, error_type=type(exc).__name__)
            raise redis_error_to_memory_error(exc) from exc

    async def fetch_recent_messages(self, session_id: str, limit: int | None = None) -> list[ChatMessage]:
        await self._ensure_session(session_id)
        resolved_limit = limit or self.config.max_messages
        try:
            raw_messages = await get_redis_memory_client().lrange(self.messages_key(session_id), -resolved_limit, -1)
            messages = [json_to_model(raw, ChatMessage) for raw in raw_messages]
            parsed = [message for message in messages if message is not None]
            log_event("short_term_messages_fetched", session_id=session_id, message_count=len(parsed))
            return parsed
        except RedisError as exc:
            raise redis_error_to_memory_error(exc) from exc

    async def update_memory(self, session: SessionState, messages: list[ChatMessage]) -> None:
        await self.store_session(session)
        for message in messages:
            await self.store_message(message)

    async def clear_session(self, session_id: str) -> bool:
        session = await self.fetch_session(session_id)
        try:
            deleted = await get_redis_memory_client().delete(self.session_key(session_id), self.messages_key(session_id))
            if session:
                await get_redis_memory_client().srem(self.user_sessions_key(session.user_id), session_id)
            log_event("short_term_session_cleared", session_id=session_id, deleted_count=deleted)
            return deleted > 0
        except RedisError as exc:
            raise redis_error_to_memory_error(exc) from exc

    async def delete_memory(self, session_id: str) -> bool:
        return await self.clear_session(session_id)

    async def _ensure_session(self, session_id: str) -> None:
        if await self.fetch_session(session_id) is None:
            raise InvalidSessionError("session not found or expired", details={"session_id": session_id})
