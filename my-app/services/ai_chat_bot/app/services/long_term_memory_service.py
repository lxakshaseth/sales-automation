from app.long_term_memory.long_term_memory_manager import LongTermMemoryManager
from app.models.long_term_memory_models import LongTermMemorySnapshot, MemoryInsight, UserMemoryProfile


class LongTermMemoryService:
    """Internal service facade for R7 MongoDB permanent memory."""

    def __init__(self, *, manager: LongTermMemoryManager | None = None) -> None:
        self.manager = manager or LongTermMemoryManager()

    async def save_conversation_memory(
        self,
        *,
        user_id: str,
        summary: str,
        session_id: str | None = None,
        conversation_id: str | None = None,
        intents: list[str] | None = None,
        entities: dict | None = None,
        language: str | None = None,
        metadata: dict | None = None,
    ) -> LongTermMemorySnapshot:
        return await self.manager.save_conversation_memory(
            user_id=user_id,
            summary=summary,
            session_id=session_id,
            conversation_id=conversation_id,
            intents=intents,
            entities=entities,
            language=language,
            metadata=metadata,
        )

    async def save_insight(self, insight: MemoryInsight) -> MemoryInsight:
        return await self.manager.save_insight(insight)

    async def get_user_memory(self, user_id: str, *, summary_limit: int = 10, insight_limit: int = 20) -> LongTermMemorySnapshot:
        return await self.manager.get_user_memory(user_id, summary_limit=summary_limit, insight_limit=insight_limit)

    async def get_profile(self, user_id: str) -> UserMemoryProfile | None:
        return await self.manager.get_profile(user_id)

    async def delete_user_memory(self, user_id: str) -> bool:
        return await self.manager.delete_user_memory(user_id)
