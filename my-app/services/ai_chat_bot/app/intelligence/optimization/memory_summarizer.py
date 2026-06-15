from typing import Any

from app.core.logger import log_error, log_event
from app.intelligence.optimization.models import MemorySummary, TokenUsage
from app.utils.token_helpers import estimate_tokens, trim_text_to_token_limit


class MemorySummarizer:
    """Compresses long conversations while preserving operational facts."""

    IMPORTANT_MARKERS = ("goal", "need", "want", "budget", "timeline", "decision", "decided", "crm", "lead", "email", "meeting", "task", "follow")

    async def summarize_history(self, history: list[dict[str, Any]], *, token_limit: int, model_name: str | None = None) -> MemorySummary:
        try:
            important = [message for message in history if self._is_important(message)]
            if not important:
                important = history[-5:]

            lines = [self._format_message(message) for message in important if self._format_message(message)]
            summary_text = trim_text_to_token_limit(" | ".join(lines), token_limit, model_name=model_name) or "No durable conversation memory."
            original_tokens = sum(estimate_tokens(self._format_message(message), model_name=model_name) for message in history)
            summary_tokens = estimate_tokens(summary_text, model_name=model_name)
            log_event("history_summarized", original_messages=len(history), summarized_messages=len(important), summary_tokens=summary_tokens)
            return MemorySummary(
                summary=summary_text,
                preserved_goals=self._extract_by_keywords(history, ("goal", "need", "want")),
                preserved_decisions=self._extract_by_keywords(history, ("decision", "decided", "approved")),
                crm_notes=self._extract_by_keywords(history, ("crm", "lead", "budget", "timeline")),
                active_tasks=self._extract_by_keywords(history, ("task", "follow", "meeting", "email")),
                original_message_count=len(history),
                summarized_message_count=len(important),
                token_usage=TokenUsage(history_tokens=original_tokens, memory_summary_tokens=summary_tokens),
            )
        except Exception as exc:
            log_error("History summarization failed", exc_info=True, error_type=type(exc).__name__)
            fallback = trim_text_to_token_limit(" ".join(self._format_message(message) for message in history[-3:]), token_limit, model_name=model_name)
            return MemorySummary(
                summary=fallback or "Conversation summary unavailable.",
                original_message_count=len(history),
                summarized_message_count=min(3, len(history)),
                token_usage=TokenUsage(memory_summary_tokens=estimate_tokens(fallback, model_name=model_name)),
            )

    async def compress_conversation(self, history: list[dict[str, Any]], *, token_limit: int, model_name: str | None = None) -> MemorySummary:
        return await self.summarize_history(history, token_limit=token_limit, model_name=model_name)

    async def build_memory_snapshot(self, history: list[dict[str, Any]], *, token_limit: int, model_name: str | None = None) -> dict[str, Any]:
        summary = await self.summarize_history(history, token_limit=token_limit, model_name=model_name)
        return {
            "summary": summary.summary,
            "goals": summary.preserved_goals,
            "decisions": summary.preserved_decisions,
            "crm_notes": summary.crm_notes,
            "active_tasks": summary.active_tasks,
        }

    def _is_important(self, message: dict[str, Any]) -> bool:
        content = self._format_message(message).lower()
        return any(marker in content for marker in self.IMPORTANT_MARKERS)

    def _format_message(self, message: dict[str, Any]) -> str:
        role = str(message.get("role") or "").strip()
        content = str(message.get("content") or message.get("message") or message.get("text") or "").strip()
        return f"{role}: {content}" if role else content

    def _extract_by_keywords(self, history: list[dict[str, Any]], keywords: tuple[str, ...]) -> list[str]:
        matches = []
        for message in history:
            text = self._format_message(message)
            if any(keyword in text.lower() for keyword in keywords):
                matches.append(trim_text_to_token_limit(text, 40))
        return matches[:5]
