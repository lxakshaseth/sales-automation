from datetime import UTC, datetime

from pymongo import ASCENDING, DESCENDING, ReturnDocument

from app.core.logger import log_event
from app.exceptions.long_term_memory_exceptions import MemoryNotFoundError
from app.models.long_term_memory_models import (
    ConversationSummaryMemory,
    LongTermMemoryConfig,
    MemoryInsight,
    UserMemoryProfile,
)
from app.utils.mongo_memory_helpers import get_mongo_memory_database, run_mongo, serialize_mongo_document


class MongoLongTermMemoryStore:
    """MongoDB repository for permanent AI memory collections."""

    _indexes_created = False

    def __init__(self, config: LongTermMemoryConfig | None = None) -> None:
        self.config = config or LongTermMemoryConfig()

    def _profiles(self):
        return get_mongo_memory_database()[self.config.profile_collection]

    def _summaries(self):
        return get_mongo_memory_database()[self.config.summary_collection]

    def _insights(self):
        return get_mongo_memory_database()[self.config.insight_collection]

    async def ensure_indexes(self) -> None:
        if self.__class__._indexes_created:
            return

        def create_indexes() -> None:
            self._profiles().create_index([("user_id", ASCENDING)], unique=True)
            self._profiles().create_index([("updated_at", DESCENDING)])
            self._summaries().create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
            self._summaries().create_index([("session_id", ASCENDING)])
            self._insights().create_index([("user_id", ASCENDING), ("importance", DESCENDING), ("updated_at", DESCENDING)])
            self._insights().create_index([("insight_id", ASCENDING)], unique=True)
            self._insights().create_index([("tags", ASCENDING)])

        await run_mongo(create_indexes)
        self.__class__._indexes_created = True
        log_event("long_term_memory_indexes_ready")

    async def upsert_profile(self, profile: UserMemoryProfile) -> UserMemoryProfile:
        await self.ensure_indexes()
        now = datetime.now(UTC)
        document = profile.model_dump(mode="python")
        document["updated_at"] = now

        def upsert():
            return self._profiles().find_one_and_update(
                {"user_id": profile.user_id},
                {"$set": document, "$setOnInsert": {"created_at": profile.created_at}},
                upsert=True,
                return_document=ReturnDocument.AFTER,
            )

        saved = serialize_mongo_document(await run_mongo(upsert))
        log_event("long_term_profile_upserted", user_id=profile.user_id)
        return UserMemoryProfile.model_validate(saved)

    async def get_profile(self, user_id: str) -> UserMemoryProfile | None:
        await self.ensure_indexes()
        document = await run_mongo(self._profiles().find_one, {"user_id": user_id})
        if not document:
            return None
        return UserMemoryProfile.model_validate(serialize_mongo_document(document))

    async def save_summary(self, summary: ConversationSummaryMemory) -> ConversationSummaryMemory:
        await self.ensure_indexes()
        document = summary.model_dump(mode="python")
        await run_mongo(self._summaries().update_one, {"summary_id": summary.summary_id}, {"$set": document}, upsert=True)
        log_event("long_term_summary_saved", user_id=summary.user_id, summary_id=summary.summary_id)
        return summary

    async def save_insight(self, insight: MemoryInsight) -> MemoryInsight:
        await self.ensure_indexes()
        if insight.confidence < self.config.min_insight_confidence:
            return insight
        document = insight.model_dump(mode="python")
        await run_mongo(self._insights().update_one, {"insight_id": insight.insight_id}, {"$set": document}, upsert=True)
        log_event("long_term_insight_saved", user_id=insight.user_id, insight_type=insight.insight_type)
        return insight

    async def get_recent_summaries(self, user_id: str, limit: int = 10) -> list[ConversationSummaryMemory]:
        await self.ensure_indexes()

        def fetch():
            return list(
                self._summaries()
                .find({"user_id": user_id}, {"_id": 1, "summary_id": 1, "user_id": 1, "session_id": 1, "summary": 1, "created_at": 1, "metadata": 1})
                .sort("created_at", DESCENDING)
                .limit(max(1, min(limit, 100)))
            )

        documents = await run_mongo(fetch)
        return [ConversationSummaryMemory.model_validate(serialize_mongo_document(document)) for document in documents]

    async def get_top_insights(self, user_id: str, limit: int = 20) -> list[MemoryInsight]:
        await self.ensure_indexes()

        def fetch():
            return list(
                self._insights()
                .find({"user_id": user_id}, {"_id": 1, "insight_id": 1, "user_id": 1, "insight_type": 1, "content": 1, "importance": 1, "confidence": 1, "tags": 1, "updated_at": 1, "created_at": 1})
                .sort([("importance", DESCENDING), ("updated_at", DESCENDING)])
                .limit(max(1, min(limit, 100)))
            )

        documents = await run_mongo(fetch)
        return [MemoryInsight.model_validate(serialize_mongo_document(document)) for document in documents]

    async def delete_user_memory(self, user_id: str) -> bool:
        await self.ensure_indexes()

        def delete() -> int:
            deleted = 0
            deleted += self._profiles().delete_many({"user_id": user_id}).deleted_count
            deleted += self._summaries().delete_many({"user_id": user_id}).deleted_count
            deleted += self._insights().delete_many({"user_id": user_id}).deleted_count
            return deleted

        deleted_count = await run_mongo(delete)
        if deleted_count == 0:
            raise MemoryNotFoundError("no long-term memory found", details={"user_id": user_id})
        log_event("long_term_user_memory_deleted", user_id=user_id, deleted_count=deleted_count)
        return True
