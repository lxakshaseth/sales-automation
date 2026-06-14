from app.memory.memory_cleanup import MemoryCleanup
from app.memory.summary_manager import SummaryManager
from app.memory.token_optimizer import TokenOptimizer
from app.models.message_models import ChatMessage
from app.models.optimization_models import MemoryOptimizationResult
from app.models.summary_models import SummarizationConfig


class MemoryOptimizer:
    """Coordinate token reduction, summarization, and cleanup for long chats."""

    def __init__(
        self,
        *,
        summary_manager: SummaryManager | None = None,
        token_optimizer: TokenOptimizer | None = None,
        cleanup: MemoryCleanup | None = None,
    ) -> None:
        self.summary_manager = summary_manager or SummaryManager()
        self.token_optimizer = token_optimizer or TokenOptimizer()
        self.cleanup = cleanup or MemoryCleanup()

    async def optimize_long_conversation(
        self,
        *,
        user_id: str,
        session_id: str | None,
        messages: list[ChatMessage],
        config: SummarizationConfig | None = None,
    ) -> MemoryOptimizationResult:
        resolved_config = config or SummarizationConfig()
        summary = await self.summary_manager.summarize_and_store(
            user_id=user_id,
            session_id=session_id,
            messages=messages,
            config=resolved_config,
        )
        return MemoryOptimizationResult(
            success=True,
            user_id=user_id,
            session_id=session_id,
            original_message_count=len(messages),
            retained_message_count=resolved_config.preserve_recent_messages,
            summarized_message_count=max(0, len(messages) - resolved_config.preserve_recent_messages),
            token_usage=summary.token_usage,
            summary_id=summary.summary_id,
            cleanup_actions=["summary_created"],
        )
