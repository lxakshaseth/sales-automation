from difflib import SequenceMatcher
from typing import Any

from app.core.logger import log_error, log_event
from app.intelligence.optimization.models import CompressionResult
from app.utils.token_helpers import estimate_tokens, trim_text_to_token_limit


class ContextCompressor:
    """Reduces duplicate and low-value context before model routing."""

    def compress_context(self, context: list[dict[str, Any]], *, token_limit: int, model_name: str | None = None) -> CompressionResult:
        try:
            original_tokens = self._count_items(context, model_name=model_name)
            deduped, duplicate_count = self.remove_duplicates(context)
            compressed = self.remove_redundant_chunks(deduped)
            trimmed = self._trim_items(compressed, token_limit=token_limit, model_name=model_name)
            compressed_tokens = self._count_items(trimmed, model_name=model_name)
            saved = max(0, original_tokens - compressed_tokens)
            ratio = round((saved / original_tokens) * 100, 2) if original_tokens else 0.0
            log_event("context_compressed", original_tokens=original_tokens, compressed_tokens=compressed_tokens, saved_tokens=saved, duplicate_removed=duplicate_count)
            return CompressionResult(
                success=True,
                original_tokens=original_tokens,
                compressed_tokens=compressed_tokens,
                saved_tokens=saved,
                compression_ratio=ratio,
                duplicate_removed=duplicate_count,
                output=trimmed,
            )
        except Exception as exc:
            log_error("Context compression failed", exc_info=True, error_type=type(exc).__name__)
            return CompressionResult(success=False, output=context, warnings=["context_compression_failed"])

    def remove_duplicates(self, items: list[dict[str, Any]], *, similarity_threshold: float = 0.95) -> tuple[list[dict[str, Any]], int]:
        retained: list[dict[str, Any]] = []
        duplicate_count = 0
        for item in items:
            content = self._content(item)
            if any(self._similarity(content, self._content(existing)) >= similarity_threshold for existing in retained):
                duplicate_count += 1
                continue
            retained.append(item)
        if duplicate_count:
            log_event("context_duplicates_removed", duplicate_count=duplicate_count)
        return retained, duplicate_count

    def remove_redundant_chunks(self, chunks: list[dict[str, Any]], *, min_score: float = 0.50) -> list[dict[str, Any]]:
        retained = [chunk for chunk in chunks if float(chunk.get("score", chunk.get("relevance", 1.0)) or 0.0) >= min_score]
        dropped = len(chunks) - len(retained)
        if dropped:
            log_event("rag_low_value_chunks_removed", dropped_chunks=dropped, min_score=min_score)
        return sorted(retained, key=lambda chunk: float(chunk.get("score", chunk.get("relevance", 0.0)) or 0.0), reverse=True)

    def optimize_rag_context(self, chunks: list[dict[str, Any]], *, token_limit: int, model_name: str | None = None) -> CompressionResult:
        return self.compress_context(chunks, token_limit=token_limit, model_name=model_name)

    def optimize_history(self, history: list[dict[str, Any]], *, token_limit: int, model_name: str | None = None) -> CompressionResult:
        important = [message for message in history if not self._is_low_value_message(message)]
        recent_first = list(reversed(important))
        trimmed = list(reversed(self._trim_items(recent_first, token_limit=token_limit, model_name=model_name)))
        original_tokens = self._count_items(history, model_name=model_name)
        compressed_tokens = self._count_items(trimmed, model_name=model_name)
        saved = max(0, original_tokens - compressed_tokens)
        return CompressionResult(
            success=True,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            saved_tokens=saved,
            compression_ratio=round((saved / original_tokens) * 100, 2) if original_tokens else 0.0,
            duplicate_removed=max(0, len(history) - len(important)),
            output=trimmed,
        )

    def _trim_items(self, items: list[dict[str, Any]], *, token_limit: int, model_name: str | None = None) -> list[dict[str, Any]]:
        retained: list[dict[str, Any]] = []
        used = 0
        for item in items:
            content = self._content(item)
            tokens = estimate_tokens(content, model_name=model_name)
            if used + tokens <= token_limit:
                retained.append(item)
                used += tokens
                continue
            remaining = max(0, token_limit - used)
            if remaining > 0:
                copy = dict(item)
                key = "content" if "content" in copy else "text"
                copy[key] = trim_text_to_token_limit(content, remaining, model_name=model_name)
                retained.append(copy)
            break
        return retained

    def _count_items(self, items: list[dict[str, Any]], *, model_name: str | None = None) -> int:
        return sum(estimate_tokens(self._content(item), model_name=model_name) for item in items)

    def _content(self, item: dict[str, Any]) -> str:
        return str(item.get("content") or item.get("text") or item.get("message") or item)

    def _similarity(self, left: str, right: str) -> float:
        if not left or not right:
            return 0.0
        return SequenceMatcher(None, left.lower(), right.lower()).ratio()

    def _is_low_value_message(self, message: dict[str, Any]) -> bool:
        content = self._content(message).strip().lower()
        low_value = {"hi", "hello", "hey", "thanks", "thank you", "ok", "okay", "yes", "no"}
        return content in low_value or len(content) <= 2
