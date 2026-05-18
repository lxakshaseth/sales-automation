from app.memory.summary_manager import SummaryManager
from app.memory.summarizer import MemorySummarizer
from app.models.message_models import ChatMessage
from app.models.summary_models import ConversationSummary, SummarizationConfig


class SummarizationService:
    """Internal service facade for R8 memory summarization."""

    def __init__(self, *, summarizer: MemorySummarizer | None = None, summary_manager: SummaryManager | None = None) -> None:
        self.summarizer = summarizer or MemorySummarizer()
        self.summary_manager = summary_manager or SummaryManager(summarizer=self.summarizer)

    async def summarize_messages(
        self,
        *,
        user_id: str,
        session_id: str | None,
        messages: list[ChatMessage],
        config: SummarizationConfig | None = None,
    ) -> ConversationSummary:
        return await self.summarizer.summarize_conversation(
            user_id=user_id,
            session_id=session_id,
            messages=messages,
            config=config,
        )

    async def summarize_and_store(
        self,
        *,
        user_id: str,
        session_id: str | None,
        messages: list[ChatMessage],
        config: SummarizationConfig | None = None,
    ) -> ConversationSummary:
        return await self.summary_manager.summarize_and_store(
            user_id=user_id,
            session_id=session_id,
            messages=messages,
            config=config,
        )
