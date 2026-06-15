from app.core.logger import log_error, log_event
from app.exceptions.summarization_exceptions import SummaryRepositoryError
from app.models.summary_models import ConversationSummary
from app.services.long_term_memory_service import LongTermMemoryService


class SummaryRepository:
    """Persist R8 summaries into R7 long-term Mongo memory."""

    def __init__(self, *, long_term_memory_service: LongTermMemoryService | None = None) -> None:
        self.long_term_memory_service = long_term_memory_service or LongTermMemoryService()

    async def store_summary(self, summary: ConversationSummary) -> str:
        try:
            snapshot = await self.long_term_memory_service.save_conversation_memory(
                user_id=summary.user_id,
                session_id=summary.session_id,
                summary=summary.summary_text,
                intents=summary.important_topics,
                language=summary.metadata.language,
                metadata={
                    "r8_summary_id": summary.summary_id,
                    "semantic_tags": summary.semantic_tags,
                    "compression_ratio": summary.compression_ratio,
                    "token_count": summary.token_count,
                },
            )
            log_event("memory_summary_persisted", user_id=summary.user_id, summary_id=summary.summary_id)
            return snapshot.summaries[0].summary_id if snapshot.summaries else summary.summary_id
        except Exception as exc:
            log_error("Memory summary persistence failed", user_id=summary.user_id, error_type=type(exc).__name__)
            raise SummaryRepositoryError("failed to persist memory summary", details={"error_type": type(exc).__name__}) from exc
