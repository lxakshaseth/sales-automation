from datetime import datetime, timezone

from app.models.long_term_memory_models import (
    ConversationSummaryMemory,
    LongTermMemoryConfig,
    MemoryInsight,
    UserMemoryProfile,
    UserPreference,
)
from app.utils.long_term_memory_helpers import merge_unique_limited, top_recurring_intents


class UserProfileBuilder:
    """Merge summaries, preferences, and insights into a stable user profile."""

    def __init__(self, config: LongTermMemoryConfig | None = None) -> None:
        self.config = config or LongTermMemoryConfig()

    def build_updated_profile(
        self,
        *,
        user_id: str,
        existing: UserMemoryProfile | None,
        summary: ConversationSummaryMemory | None = None,
        preferences: dict[str, UserPreference] | None = None,
        insights: list[MemoryInsight] | None = None,
    ) -> UserMemoryProfile:
        profile = existing or UserMemoryProfile(user_id=user_id)
        resolved_preferences = dict(profile.preferences)
        resolved_preferences.update(preferences or {})

        facts = [insight.content for insight in insights or [] if insight.insight_type in {"fact", "business_context", "semantic_note"}]
        known_facts = merge_unique_limited(profile.known_facts, facts, limit=self.config.max_profile_facts)
        recurring_intents = top_recurring_intents(profile.recurring_intents, summary.intents if summary else [], limit=self.config.max_recurring_intents)
        semantic_profile = self._semantic_profile(summary=summary, insights=insights or [], existing=profile.semantic_profile)

        return profile.model_copy(
            update={
                "preferences": resolved_preferences,
                "known_facts": known_facts,
                "recurring_intents": recurring_intents,
                "semantic_profile": semantic_profile,
                "last_summary": summary.summary if summary else profile.last_summary,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def _semantic_profile(self, *, summary: ConversationSummaryMemory | None, insights: list[MemoryInsight], existing: str) -> str:
        parts = [existing.strip()] if existing.strip() else []
        if summary:
            parts.append(summary.summary.strip())
        parts.extend(insight.content.strip() for insight in insights if insight.importance >= 0.5)
        compact = " ".join(part for part in parts if part)
        return compact[-4000:]
