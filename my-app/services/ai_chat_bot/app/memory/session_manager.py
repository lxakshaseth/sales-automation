from datetime import datetime, timezone

from app.core.logger import log_event
from app.exceptions.memory_exceptions import InvalidSessionError
from app.memory.memory_cache import MemoryCache
from app.memory.redis_memory import RedisMemoryStore
from app.memory.ttl_manager import TTLManager
from app.models.memory_models import MemoryConfig
from app.models.session_models import SessionMetadata, SessionState


class SessionManager:
    """Manage active UUID-based short-term memory sessions."""

    def __init__(
        self,
        *,
        store: RedisMemoryStore | None = None,
        cache: MemoryCache | None = None,
        config: MemoryConfig | None = None,
    ) -> None:
        self.config = config or MemoryConfig()
        self.store = store or RedisMemoryStore(self.config)
        self.cache = cache or MemoryCache()
        self.ttl_manager = TTLManager(self.config)

    async def create_session(self, user_id: str, metadata: SessionMetadata | None = None) -> SessionState:
        session = SessionState(user_id=user_id, metadata=metadata or SessionMetadata(), expires_at=self.ttl_manager.expires_at())
        await self.store.store_session(session)
        await self.cache.set_session(session)
        log_event("short_term_session_created", session_id=session.session_id, user_id=user_id)
        return session

    async def get_session(self, session_id: str) -> SessionState:
        cached = await self.cache.get_session(session_id)
        if cached:
            return cached
        session = await self.store.fetch_session(session_id)
        if session is None:
            raise InvalidSessionError("session not found or expired", details={"session_id": session_id})
        await self.cache.set_session(session)
        return session

    async def touch_session(self, session_id: str) -> SessionState:
        session = await self.get_session(session_id)
        updated = session.model_copy(update={"updated_at": datetime.now(timezone.utc), "expires_at": self.ttl_manager.expires_at()})
        await self.store.store_session(updated)
        await self.cache.set_session(updated)
        return updated

    async def close_session(self, session_id: str) -> bool:
        await self.cache.invalidate(session_id)
        return await self.store.clear_session(session_id)
