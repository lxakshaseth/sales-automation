import asyncio
from collections import OrderedDict

from app.models.memory_models import ConversationMemory
from app.models.session_models import SessionState


class MemoryCache:
    """Process-local hot cache; Redis remains the source of truth."""

    def __init__(self, *, max_entries: int = 2_000) -> None:
        self.max_entries = max_entries
        self._sessions: OrderedDict[str, SessionState] = OrderedDict()
        self._context: OrderedDict[str, ConversationMemory] = OrderedDict()
        self._lock = asyncio.Lock()

    async def get_session(self, session_id: str) -> SessionState | None:
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                self._sessions.move_to_end(session_id)
            return session

    async def set_session(self, session: SessionState) -> None:
        async with self._lock:
            self._sessions[session.session_id] = session
            self._sessions.move_to_end(session.session_id)
            await self._trim(self._sessions)

    async def get_conversation(self, session_id: str) -> ConversationMemory | None:
        async with self._lock:
            memory = self._context.get(session_id)
            if memory:
                self._context.move_to_end(session_id)
            return memory

    async def set_conversation(self, memory: ConversationMemory) -> None:
        async with self._lock:
            self._context[memory.session.session_id] = memory
            self._context.move_to_end(memory.session.session_id)
            await self._trim(self._context)

    async def invalidate(self, session_id: str) -> None:
        async with self._lock:
            self._sessions.pop(session_id, None)
            self._context.pop(session_id, None)

    async def _trim(self, cache: OrderedDict) -> None:
        while len(cache) > self.max_entries:
            cache.popitem(last=False)
