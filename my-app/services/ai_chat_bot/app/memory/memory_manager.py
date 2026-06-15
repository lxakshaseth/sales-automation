from datetime import UTC, datetime

from app.core.logger import log_error, log_event
from app.exceptions.memory_exceptions import MemoryError
from app.memory.context_window import ContextWindowManager
from app.memory.memory_cache import MemoryCache
from app.memory.redis_memory import RedisMemoryStore
from app.memory.session_manager import SessionManager
from app.models.memory_models import ConversationMemory, MemoryConfig
from app.models.message_models import ChatMessage, MessageRole
from app.models.session_models import SessionMetadata, SessionState
from app.utils.context_helpers import estimate_message_tokens


class MemoryManager:
    """Orchestrate Redis short-term memory for active AI conversations."""

    def __init__(
        self,
        *,
        config: MemoryConfig | None = None,
        store: RedisMemoryStore | None = None,
        session_manager: SessionManager | None = None,
        context_window_manager: ContextWindowManager | None = None,
        cache: MemoryCache | None = None,
    ) -> None:
        self.config = config or MemoryConfig()
        self.store = store or RedisMemoryStore(self.config)
        self.cache = cache or MemoryCache()
        self.session_manager = session_manager or SessionManager(store=self.store, cache=self.cache, config=self.config)
        self.context_window_manager = context_window_manager or ContextWindowManager(self.config)

    async def start_session(self, user_id: str, metadata: SessionMetadata | None = None) -> SessionState:
        return await self.session_manager.create_session(user_id, metadata)

    async def store_message(
        self,
        *,
        session_id: str,
        user_id: str,
        role: MessageRole,
        message_text: str,
        metadata: dict | None = None,
        message_id: str | None = None,
    ) -> ChatMessage:
        try:
            session = await self.session_manager.touch_session(session_id)
            token_count = estimate_message_tokens(message_text)
            message = ChatMessage(
                **({"message_id": message_id} if message_id else {}),
                session_id=session_id,
                user_id=user_id,
                role=role,
                message_text=message_text,
                token_count=token_count,
                metadata=metadata or {},
            )
            stored = await self.store.store_message(message)
            updated_session = session.model_copy(
                update={
                    "message_count": session.message_count + 1,
                    "updated_at": datetime.now(UTC),
                }
            )
            await self.store.store_session(updated_session)
            await self.cache.invalidate(session_id)
            log_event("short_term_memory_updated", session_id=session_id, user_id=user_id, role=role)
            return stored
        except MemoryError:
            raise
        except Exception as exc:
            log_error("Short-term memory update failed", session_id=session_id, error_type=type(exc).__name__)
            raise MemoryError("failed to store short-term memory", details={"error_type": type(exc).__name__}) from exc

    async def get_conversation_memory(self, session_id: str) -> ConversationMemory:
        cached = await self.cache.get_conversation(session_id)
        if cached:
            return cached
        session = await self.session_manager.get_session(session_id)
        recent_messages = await self.store.fetch_recent_messages(session_id, limit=max(self.config.max_messages * 4, self.config.max_messages))
        context_window = await self.context_window_manager.build_window(
            session_id=session.session_id,
            user_id=session.user_id,
            messages=recent_messages,
        )
        memory = ConversationMemory(session=session, context_window=context_window, recent_messages=recent_messages)
        await self.cache.set_conversation(memory)
        log_event("short_term_context_retrieved", session_id=session_id, message_count=len(context_window.messages))
        return memory

    async def clear_session(self, session_id: str) -> bool:
        await self.cache.invalidate(session_id)
        return await self.store.clear_session(session_id)
