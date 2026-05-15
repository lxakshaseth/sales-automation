import asyncio
from collections import defaultdict

from app.models.message_models import ChatMessage


class MessageBuffer:
    """Async-safe temporary buffer for future streaming and batched writes."""

    def __init__(self) -> None:
        self._messages: dict[str, list[ChatMessage]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def add(self, message: ChatMessage) -> None:
        async with self._lock:
            self._messages[message.session_id].append(message)

    async def drain(self, session_id: str) -> list[ChatMessage]:
        async with self._lock:
            messages = list(self._messages.get(session_id, []))
            self._messages.pop(session_id, None)
            return messages
