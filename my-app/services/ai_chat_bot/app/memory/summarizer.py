import json

from app.config.settings import settings
from app.core.logger import log_error, log_event
from app.exceptions.summarization_exceptions import EmptyConversationError, SummaryGenerationError
from app.memory.compression import CompressionEngine
from app.memory.token_optimizer import TokenOptimizer
from app.models.compression_models import CompressedContext
from app.models.message_models import ChatMessage
from app.models.summary_models import ConversationSummary, SummarizationConfig, SummaryMetadata
from app.services.groq_service import GroqServiceError, _get_groq_client
from app.utils.memory_helpers import compression_ratio
from app.utils.summarization_helpers import extract_keywords, parse_summary_json


MEMORY_SUMMARY_PROMPT = """
Summarize this conversation for long-term AI memory.
Return only JSON with:
summary: compact paragraph preserving user facts, preferences, project details, decisions, open questions, and intent.
important_topics: short list.
semantic_tags: short list.
Remove greetings, repeated text, and irrelevant small talk.
Support English, Hindi, and Hinglish. Keep meaning precise.
""".strip()


class MemorySummarizer:
    """Generate compact semantic memory summaries from compressed conversations."""

    def __init__(
        self,
        *,
        compression_engine: CompressionEngine | None = None,
        token_optimizer: TokenOptimizer | None = None,
    ) -> None:
        self.compression_engine = compression_engine or CompressionEngine()
        self.token_optimizer = token_optimizer or TokenOptimizer()

    async def summarize_conversation(
        self,
        *,
        user_id: str,
        session_id: str | None,
        messages: list[ChatMessage],
        config: SummarizationConfig | None = None,
    ) -> ConversationSummary:
        resolved_config = config or SummarizationConfig()
        compressed_result = await self.compression_engine.compress_messages(
            user_id=user_id,
            session_id=session_id,
            messages=messages,
            config=resolved_config,
        )
        if not compressed_result.success or compressed_result.compressed_context is None:
            raise SummaryGenerationError("compression failed before summarization", details=compressed_result.error or {})
        return await self.generate_summary(user_id=user_id, session_id=session_id, compressed_context=compressed_result.compressed_context, config=resolved_config)

    async def summarize_messages(self, messages: list[ChatMessage], *, user_id: str, session_id: str | None = None) -> ConversationSummary:
        return await self.summarize_conversation(user_id=user_id, session_id=session_id, messages=messages)

    async def generate_summary(
        self,
        *,
        user_id: str,
        session_id: str | None,
        compressed_context: CompressedContext,
        config: SummarizationConfig,
    ) -> ConversationSummary:
        if not compressed_context.compressed_text.strip():
            raise EmptyConversationError()

        log_event("memory_summarization_started", user_id=user_id, session_id=session_id)
        if config.use_llm:
            try:
                summary_payload = await self._generate_llm_summary(compressed_context.compressed_text, config)
            except (GroqServiceError, Exception) as exc:
                log_error("Groq memory summarization failed; using extractive fallback", user_id=user_id, error_type=type(exc).__name__)
                summary_payload = self._fallback_summary(compressed_context.compressed_text)
        else:
            summary_payload = self._fallback_summary(compressed_context.compressed_text)

        summary_text = self.optimize_summary(str(summary_payload.get("summary", "")), config)
        topics = [str(item) for item in summary_payload.get("important_topics", [])][:10]
        tags = [str(item) for item in summary_payload.get("semantic_tags", [])][:12] or extract_keywords(summary_text)
        token_usage = self.token_optimizer.usage(input_text=compressed_context.compressed_text, output_text=summary_text, config=config)
        metadata = SummaryMetadata(
            user_id=user_id,
            session_id=session_id,
            source_message_count=compressed_context.metadata.get("source_message_count", 0),
            source_token_count=token_usage.input_tokens,
            summary_token_count=token_usage.output_tokens,
            compression_ratio=compression_ratio(token_usage.input_tokens, token_usage.output_tokens),
            model_name=config.model_name,
            language=config.language_hint,
        )
        summary = ConversationSummary(
            user_id=user_id,
            session_id=session_id,
            summary_text=summary_text,
            important_topics=topics,
            semantic_tags=tags,
            token_count=token_usage.output_tokens,
            source_message_count=metadata.source_message_count,
            compression_ratio=metadata.compression_ratio,
            token_usage=token_usage,
            metadata=metadata,
        )
        log_event("memory_summary_generated", user_id=user_id, session_id=session_id, summary_id=summary.summary_id)
        return summary

    def optimize_summary(self, summary_text: str, config: SummarizationConfig) -> str:
        return self.token_optimizer.trim_to_budget(summary_text, config.model_copy(update={"max_input_tokens": config.max_summary_tokens}))

    async def _generate_llm_summary(self, transcript: str, config: SummarizationConfig) -> dict:
        response = await _get_groq_client().chat.completions.create(
            model=config.model_name or settings.groq_model,
            messages=[
                {"role": "system", "content": MEMORY_SUMMARY_PROMPT},
                {"role": "user", "content": json.dumps({"conversation": transcript}, ensure_ascii=False)},
            ],
            temperature=0.1,
            max_tokens=config.max_summary_tokens,
            response_format={"type": "json_object"},
        )
        return parse_summary_json(response.choices[0].message.content or "{}")

    def _fallback_summary(self, transcript: str) -> dict:
        compact = " ".join(line.strip() for line in transcript.splitlines() if line.strip())
        return {
            "summary": compact[:1800] or "No meaningful conversation content was available.",
            "important_topics": extract_keywords(compact, limit=8),
            "semantic_tags": extract_keywords(compact, limit=12),
        }
