from typing import Any

from app.core.logger import log_error, log_event
from app.models.context_models import MemoryContext, chat_message_to_memory_context
from app.models.long_term_memory_models import ConversationSummaryMemory, LongTermMemorySnapshot, MemoryInsight, UserMemoryProfile
from app.models.message_models import ChatMessage
from app.models.summary_models import ConversationSummary
from app.utils.context_helpers import context_fingerprint, normalize_context_text
from app.utils.token_helpers import estimate_tokens


class MemoryMerger:
    """Merge R6 short-term memory, R7 long-term memory, and R8 summaries."""

    async def merge_memory(
        self,
        *,
        short_term_memory: list[Any] | None = None,
        long_term_memory: Any | None = None,
        summarized_memory: list[Any] | None = None,
        model_name: str | None = None,
    ) -> tuple[list[MemoryContext], list[MemoryContext], list[MemoryContext]]:
        log_event("context_memory_merging_started")
        short_items = self._merge_short_term(short_term_memory or [], model_name=model_name)
        long_items = self._merge_long_term(long_term_memory, model_name=model_name)
        summary_items = self._merge_summaries(summarized_memory or [], model_name=model_name)
        log_event(
            "context_memory_merging_completed",
            short_term_count=len(short_items),
            long_term_count=len(long_items),
            summary_count=len(summary_items),
        )
        return short_items, long_items, summary_items

    def _dedupe(self, items: list[MemoryContext]) -> list[MemoryContext]:
        seen: set[str] = set()
        deduped: list[MemoryContext] = []
        for item in items:
            fingerprint = context_fingerprint(item.content)
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            deduped.append(item)
        return deduped

    def _merge_short_term(self, items: list[Any], *, model_name: str | None) -> list[MemoryContext]:
        merged: list[MemoryContext] = []
        for item in items:
            try:
                if isinstance(item, ChatMessage):
                    context = chat_message_to_memory_context(item)
                elif isinstance(item, MemoryContext):
                    context = item
                else:
                    data = item.model_dump() if hasattr(item, "model_dump") else dict(item) if isinstance(item, dict) else {}
                    content = normalize_context_text(data.get("content") or data.get("message_text") or data.get("text"))
                    if not content:
                        continue
                    context = MemoryContext(
                        memory_type="short_term_memory",
                        content=content,
                        importance=float(data.get("importance", 0.55)),
                        recency_score=float(data.get("recency_score", 0.85)),
                        confidence=float(data.get("confidence", 0.75)),
                        metadata=data.get("metadata", {}),
                    )
                context.token_count = context.token_count or estimate_tokens(context.content, model_name=model_name)
                merged.append(context)
            except Exception as exc:
                log_error("Malformed short-term memory skipped", error_type=type(exc).__name__, exc_info=True)
        return self._dedupe(merged)

    def _merge_long_term(self, memory: Any | None, *, model_name: str | None) -> list[MemoryContext]:
        if memory is None:
            return []
        items: list[MemoryContext] = []
        try:
            if isinstance(memory, LongTermMemorySnapshot):
                if memory.profile:
                    items.extend(self._profile_to_context(memory.profile, model_name=model_name))
                for insight in memory.insights:
                    items.append(self._insight_to_context(insight, model_name=model_name))
                for summary in memory.summaries:
                    items.append(self._summary_memory_to_context(summary, model_name=model_name))
            elif isinstance(memory, UserMemoryProfile):
                items.extend(self._profile_to_context(memory, model_name=model_name))
            elif isinstance(memory, list):
                for item in memory:
                    items.extend(self._merge_long_term(item, model_name=model_name))
            elif isinstance(memory, MemoryContext):
                items.append(memory)
            elif isinstance(memory, dict):
                content = normalize_context_text(memory.get("content") or memory.get("summary") or memory.get("semantic_profile"))
                if content:
                    items.append(
                        MemoryContext(
                            memory_type="long_term_memory",
                            content=content,
                            importance=float(memory.get("importance", 0.7)),
                            confidence=float(memory.get("confidence", 0.75)),
                            metadata=memory.get("metadata", {}),
                            token_count=estimate_tokens(content, model_name=model_name),
                        )
                    )
        except Exception as exc:
            log_error("Malformed long-term memory skipped", error_type=type(exc).__name__, exc_info=True)
        return self._dedupe(items)

    def _merge_summaries(self, summaries: list[Any], *, model_name: str | None) -> list[MemoryContext]:
        items: list[MemoryContext] = []
        for summary in summaries:
            try:
                if isinstance(summary, ConversationSummary):
                    content = summary.summary_text
                    metadata = {
                        "summary_id": summary.summary_id,
                        "topics": summary.important_topics,
                        "semantic_tags": summary.semantic_tags,
                    }
                elif isinstance(summary, ConversationSummaryMemory):
                    content = summary.summary
                    metadata = {"summary_id": summary.summary_id, "intents": summary.intents, "entities": summary.entities}
                elif isinstance(summary, MemoryContext):
                    items.append(summary)
                    continue
                else:
                    data = summary.model_dump() if hasattr(summary, "model_dump") else dict(summary) if isinstance(summary, dict) else {}
                    content = data.get("summary_text") or data.get("summary") or data.get("content")
                    metadata = data.get("metadata", {})
                content = normalize_context_text(content)
                if content:
                    items.append(
                        MemoryContext(
                            memory_type="summary_memory",
                            content=content,
                            importance=0.8,
                            recency_score=0.65,
                            confidence=0.8,
                            metadata=metadata,
                            token_count=estimate_tokens(content, model_name=model_name),
                        )
                    )
            except Exception as exc:
                log_error("Malformed summarized memory skipped", error_type=type(exc).__name__, exc_info=True)
        return self._dedupe(items)

    def _profile_to_context(self, profile: UserMemoryProfile, *, model_name: str | None) -> list[MemoryContext]:
        lines: list[str] = []
        if profile.semantic_profile:
            lines.append(f"Semantic profile: {profile.semantic_profile}")
        if profile.known_facts:
            lines.append("Known facts: " + "; ".join(profile.known_facts))
        if profile.recurring_intents:
            lines.append("Recurring intents: " + "; ".join(profile.recurring_intents))
        if profile.preferences:
            prefs = [f"{pref.key}: {pref.value}" for pref in profile.preferences.values()]
            lines.append("Preferences: " + "; ".join(prefs))
        content = normalize_context_text("\n".join(lines))
        if not content:
            return []
        return [
            MemoryContext(
                memory_type="long_term_memory",
                content=content,
                importance=0.85,
                confidence=0.85,
                metadata={"user_id": profile.user_id, "memory_version": profile.memory_version},
                token_count=estimate_tokens(content, model_name=model_name),
                created_at=profile.updated_at,
            )
        ]

    def _insight_to_context(self, insight: MemoryInsight, *, model_name: str | None) -> MemoryContext:
        content = normalize_context_text(f"{insight.insight_type}: {insight.content}")
        return MemoryContext(
            memory_type="long_term_memory",
            content=content,
            importance=insight.importance,
            confidence=insight.confidence,
            metadata={"insight_id": insight.insight_id, "tags": insight.tags, "source": insight.source_session_id},
            token_count=estimate_tokens(content, model_name=model_name),
            created_at=insight.updated_at,
        )

    def _summary_memory_to_context(self, summary: ConversationSummaryMemory, *, model_name: str | None) -> MemoryContext:
        content = normalize_context_text(summary.summary)
        return MemoryContext(
            memory_type="summary_memory",
            content=content,
            importance=0.8,
            confidence=0.8,
            metadata={"summary_id": summary.summary_id, "intents": summary.intents, "language": summary.language},
            token_count=estimate_tokens(content, model_name=model_name),
            created_at=summary.created_at,
        )

