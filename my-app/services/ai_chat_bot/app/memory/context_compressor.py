from app.memory.compression import CompressionEngine
from app.models.compression_models import CompressionResult
from app.models.memory_models import ConversationMemory
from app.models.summary_models import SummarizationConfig


class ContextCompressor:
    """Compress active R6 conversation memory for prompt and summary efficiency."""

    def __init__(self, *, compression_engine: CompressionEngine | None = None) -> None:
        self.compression_engine = compression_engine or CompressionEngine()

    async def compress_active_context(self, memory: ConversationMemory, config: SummarizationConfig | None = None) -> CompressionResult:
        resolved_config = config or SummarizationConfig()
        return await self.compression_engine.compress_messages(
            user_id=memory.session.user_id,
            session_id=memory.session.session_id,
            messages=memory.recent_messages,
            config=resolved_config,
        )
