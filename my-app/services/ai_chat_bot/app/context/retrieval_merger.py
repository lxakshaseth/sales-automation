from typing import Any

from app.core.logger import log_error, log_event
from app.exceptions.context_exceptions import InvalidContextError
from app.models.context_models import RetrievalContext
from app.utils.context_helpers import context_fingerprint, normalize_context_text
from app.utils.token_helpers import estimate_tokens


class RetrievalMerger:
    """Normalize, deduplicate, and order retrieved chunks from R5."""

    async def merge_retrieval(self, retrieved_items: list[Any] | None, *, model_name: str | None = None) -> list[RetrievalContext]:
        log_event("context_retrieval_merging_started", item_count=len(retrieved_items or []))
        seen: set[str] = set()
        merged: list[RetrievalContext] = []

        for item in retrieved_items or []:
            try:
                context = self._coerce_item(item, model_name=model_name)
            except Exception as exc:
                log_error("Invalid retrieval result skipped", error_type=type(exc).__name__, exc_info=True)
                continue

            fingerprint = context_fingerprint(context.content)
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            merged.append(context)

        merged.sort(key=lambda item: (item.score, -(item.rank or 999999)), reverse=True)
        log_event("context_retrieval_merging_completed", merged_count=len(merged))
        return merged

    def _coerce_item(self, item: Any, *, model_name: str | None = None) -> RetrievalContext:
        if isinstance(item, RetrievalContext):
            if item.token_count == 0:
                item.token_count = estimate_tokens(item.content, model_name=model_name)
            return item

        data = item.model_dump() if hasattr(item, "model_dump") else dict(item) if isinstance(item, dict) else {}
        content = normalize_context_text(
            data.get("content")
            or data.get("page_content")
            or data.get("text")
            or getattr(item, "page_content", "")
        )
        if not content:
            stored_vector = data.get("stored_vector")
            if stored_vector and hasattr(stored_vector, "metadata"):
                content = normalize_context_text(stored_vector.metadata.get("content", ""))
        if not content:
            raise InvalidContextError("retrieval item does not contain content")

        score = float(data.get("final_score") or data.get("score") or data.get("similarity_score") or 0.0)
        score = min(1.0, max(0.0, score))
        metadata = data.get("chunk_metadata") or data.get("metadata") or getattr(item, "metadata", {}) or {}
        return RetrievalContext(
            chunk_id=data.get("chunk_id"),
            document_id=data.get("document_id"),
            source_name=data.get("source_filename") or metadata.get("source") or metadata.get("filename"),
            content=content,
            score=score,
            rank=data.get("rank"),
            metadata=metadata | {"retrieval_metadata": data.get("retrieval_metadata", {})},
            token_count=estimate_tokens(content, model_name=model_name),
        )
