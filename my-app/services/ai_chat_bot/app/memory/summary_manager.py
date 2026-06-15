import time

from app.core.logger import log_error, log_event
from app.exceptions.summarization_exceptions import EmptyConversationError, SummarizationError
from app.memory.summarizer import MemorySummarizer
from app.memory.summary_repository import SummaryRepository
from app.models.message_models import ChatMessage
from app.models.summary_models import ConversationSummary, SummarizationConfig


class SummaryManager:
    """Orchestrate R8 summarization lifecycle and optional persistence."""

    def __init__(
        self,
        *,
        summarizer: MemorySummarizer | None = None,
        repository: SummaryRepository | None = None,
    ) -> None:
        self.summarizer = summarizer or MemorySummarizer()
        self.repository = repository or SummaryRepository()

    async def summarize_and_store(
        self,
        *,
        user_id: str,
        session_id: str | None,
        messages: list[ChatMessage],
        config: SummarizationConfig | None = None,
    ) -> ConversationSummary:
        started_at = time.perf_counter()
        resolved_config = config or SummarizationConfig()
        if len(messages) < resolved_config.min_messages_to_summarize:
            raise EmptyConversationError(
                "not enough messages to summarize",
                details={"message_count": len(messages), "min_messages": resolved_config.min_messages_to_summarize},
            )

        try:
            summary = await self.summarizer.summarize_conversation(
                user_id=user_id,
                session_id=session_id,
                messages=messages,
                config=resolved_config,
            )
            if resolved_config.store_long_term:
                await self.repository.store_summary(summary)
            log_event("memory_summary_lifecycle_completed", user_id=user_id, duration_ms=round((time.perf_counter() - started_at) * 1000, 2))
            return summary
        except SummarizationError:
            raise
        except Exception as exc:
            log_error("Memory summary lifecycle failed", user_id=user_id, error_type=type(exc).__name__)
            raise SummarizationError("summary lifecycle failed", details={"error_type": type(exc).__name__}) from exc
