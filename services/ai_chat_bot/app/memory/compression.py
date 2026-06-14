import time

from app.core.logger import log_error, log_event
from app.exceptions.summarization_exceptions import CompressionError, EmptyConversationError
from app.memory.token_optimizer import TokenOptimizer
from app.models.compression_models import CompressedContext, CompressionResult
from app.models.message_models import ChatMessage
from app.models.summary_models import SummarizationConfig
from app.utils.memory_helpers import split_messages_for_summary
from app.utils.summarization_helpers import extract_keywords, messages_to_transcript, remove_duplicate_and_small_talk


class CompressionEngine:
    """Semantic-safe pre-LLM compression for long active conversations."""

    def __init__(self, *, token_optimizer: TokenOptimizer | None = None) -> None:
        self.token_optimizer = token_optimizer or TokenOptimizer()

    async def compress_messages(
        self,
        *,
        user_id: str,
        session_id: str | None,
        messages: list[ChatMessage],
        config: SummarizationConfig,
    ) -> CompressionResult:
        started_at = time.perf_counter()
        try:
            if not messages:
                raise EmptyConversationError()

            cleaned = remove_duplicate_and_small_talk(messages)
            to_summarize, preserved = split_messages_for_summary(cleaned, preserve_recent=config.preserve_recent_messages)
            source = to_summarize or cleaned
            transcript = messages_to_transcript(source, max_tokens=config.max_input_tokens, model_name=config.model_name)
            transcript = self.token_optimizer.trim_to_budget(transcript, config)
            if not transcript:
                raise CompressionError("compressed transcript is empty")

            token_usage = self.token_optimizer.usage(input_text=messages_to_transcript(messages, max_tokens=10**9), output_text=transcript, config=config)
            compressed = CompressedContext(
                user_id=user_id,
                session_id=session_id,
                compressed_text=transcript,
                preserved_messages=preserved,
                removed_message_count=max(0, len(messages) - len(source) - len(preserved)),
                token_usage=token_usage,
                semantic_markers=extract_keywords(transcript),
                metadata={"cleaned_message_count": len(cleaned), "source_message_count": len(source)},
            )
            log_event("memory_compression_completed", user_id=user_id, session_id=session_id, compression_ratio=token_usage.compression_ratio)
            return CompressionResult(success=True, compressed_context=compressed, duration_ms=round((time.perf_counter() - started_at) * 1000, 2))
        except (CompressionError, EmptyConversationError) as exc:
            log_error("Memory compression failed", user_id=user_id, error_code=exc.error_code)
            return CompressionResult(success=False, error=exc.to_response(), duration_ms=round((time.perf_counter() - started_at) * 1000, 2))
        except Exception as exc:
            log_error("Unexpected memory compression failure", user_id=user_id, error_type=type(exc).__name__)
            error = CompressionError(details={"error_type": type(exc).__name__})
            return CompressionResult(success=False, error=error.to_response(), duration_ms=round((time.perf_counter() - started_at) * 1000, 2))
