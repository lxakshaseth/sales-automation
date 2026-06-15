from app.memory.compression import CompressionEngine
from app.memory.context_compressor import ContextCompressor
from app.models.compression_models import CompressionResult
from app.models.memory_models import ConversationMemory
from app.models.message_models import ChatMessage
from app.models.summary_models import SummarizationConfig


class CompressionService:
    """Internal service facade for context compression."""

    def __init__(self, *, compression_engine: CompressionEngine | None = None, context_compressor: ContextCompressor | None = None) -> None:
        self.compression_engine = compression_engine or CompressionEngine()
        self.context_compressor = context_compressor or ContextCompressor(compression_engine=self.compression_engine)

    async def compress_messages(
        self,
        *,
        user_id: str,
        session_id: str | None,
        messages: list[ChatMessage],
        config: SummarizationConfig | None = None,
    ) -> CompressionResult:
        return await self.compression_engine.compress_messages(
            user_id=user_id,
            session_id=session_id,
            messages=messages,
            config=config or SummarizationConfig(),
        )

    async def compress_active_context(self, memory: ConversationMemory, config: SummarizationConfig | None = None) -> CompressionResult:
        return await self.context_compressor.compress_active_context(memory, config)
