from app.core.logger import log_error, log_event
from app.exceptions.long_term_memory_exceptions import LongTermMemoryError
from app.long_term_memory.memory_extractor import MemoryExtractor
from app.long_term_memory.mongo_memory_store import MongoLongTermMemoryStore
from app.long_term_memory.profile_builder import UserProfileBuilder
from app.models.long_term_memory_models import (
    ConversationSummaryMemory,
    LongTermMemoryConfig,
    LongTermMemorySnapshot,
    MemoryInsight,
    UserMemoryProfile,
)


class LongTermMemoryManager:
    """Orchestrates permanent user memory writes and reads."""

    def __init__(
        self,
        *,
        store: MongoLongTermMemoryStore | None = None,
        extractor: MemoryExtractor | None = None,
        profile_builder: UserProfileBuilder | None = None,
        config: LongTermMemoryConfig | None = None,
    ) -> None:
        self.config = config or LongTermMemoryConfig()
        self.store = store or MongoLongTermMemoryStore(self.config)
        self.extractor = extractor or MemoryExtractor()
        self.profile_builder = profile_builder or UserProfileBuilder(self.config)

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
        try:
            summary_memory = ConversationSummaryMemory(
                user_id=user_id,
                summary=summary,
                session_id=session_id,
                conversation_id=conversation_id,
                intents=intents or [],
                entities=entities or {},
                language=language,
                metadata=metadata or {},
            )
            saved_summary = await self.store.save_summary(summary_memory)
            preferences = await self.extractor.extract_preferences(user_id=user_id, text=summary)
            insights = await self.extractor.extract_insights(user_id=user_id, text=summary, session_id=session_id)
            for insight in insights:
                await self.store.save_insight(insight)

            existing_profile = await self.store.get_profile(user_id)
            profile = self.profile_builder.build_updated_profile(
                user_id=user_id,
                existing=existing_profile,
                summary=saved_summary,
                preferences=preferences,
                insights=insights,
            )
            saved_profile = await self.store.upsert_profile(profile)
            log_event("long_term_memory_saved", user_id=user_id, insight_count=len(insights), preference_count=len(preferences))
            return LongTermMemorySnapshot(user_id=user_id, profile=saved_profile, summaries=[saved_summary], insights=insights)
        except LongTermMemoryError:
            raise
        except Exception as exc:
            log_error("Long-term memory save failed", user_id=user_id, error_type=type(exc).__name__)
            raise LongTermMemoryError("failed to save long-term memory", details={"error_type": type(exc).__name__}) from exc

    async def save_insight(self, insight: MemoryInsight) -> MemoryInsight:
        return await self.store.save_insight(insight)

    async def get_user_memory(self, user_id: str, *, summary_limit: int = 10, insight_limit: int = 20) -> LongTermMemorySnapshot:
        profile = await self.store.get_profile(user_id)
        summaries = await self.store.get_recent_summaries(user_id, limit=summary_limit)
        insights = await self.store.get_top_insights(user_id, limit=insight_limit)
        log_event("long_term_memory_retrieved", user_id=user_id, summary_count=len(summaries), insight_count=len(insights))
        return LongTermMemorySnapshot(user_id=user_id, profile=profile, summaries=summaries, insights=insights)

    async def get_profile(self, user_id: str) -> UserMemoryProfile | None:
        return await self.store.get_profile(user_id)

    async def delete_user_memory(self, user_id: str) -> bool:
        return await self.store.delete_user_memory(user_id)
