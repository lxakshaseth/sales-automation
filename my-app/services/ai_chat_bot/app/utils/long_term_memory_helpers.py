import re
from collections import Counter

from app.models.long_term_memory_models import MemoryInsight, UserPreference

PREFERENCE_PATTERNS = (
    re.compile(r"\bprefer(?:s|red)?\s+(?P<value>[^.?!]+)", re.IGNORECASE),
    re.compile(r"\bmy preference is\s+(?P<value>[^.?!]+)", re.IGNORECASE),
    re.compile(r"\bi like\s+(?P<value>[^.?!]+)", re.IGNORECASE),
)


def extract_lightweight_preferences(user_id: str, text: str) -> dict[str, UserPreference]:
    preferences: dict[str, UserPreference] = {}
    for index, pattern in enumerate(PREFERENCE_PATTERNS):
        match = pattern.search(text or "")
        if match:
            value = match.group("value").strip()[:240]
            preferences[f"preference_{index + 1}"] = UserPreference(key=f"preference_{index + 1}", value=value, confidence=0.55)
    return preferences


def extract_lightweight_insights(user_id: str, text: str, *, session_id: str | None = None) -> list[MemoryInsight]:
    content = str(text or "").strip()
    if not content:
        return []

    insights: list[MemoryInsight] = []
    lower = content.lower()
    if any(term in lower for term in ("pricing", "price", "cost", "budget")):
        insights.append(MemoryInsight(user_id=user_id, insight_type="intent", content="User has discussed pricing or budget.", source_session_id=session_id, tags=["pricing"], confidence=0.6))
    if any(term in lower for term in ("demo", "meeting", "appointment", "call")):
        insights.append(MemoryInsight(user_id=user_id, insight_type="follow_up", content="User may be interested in a demo, meeting, or appointment.", source_session_id=session_id, tags=["follow_up"], confidence=0.6))
    if any(term in lower for term in ("hindi", "hinglish", "marathi", "english")):
        insights.append(MemoryInsight(user_id=user_id, insight_type="preference", content="User language preference may be present in the conversation.", source_session_id=session_id, tags=["language"], confidence=0.5))
    return insights


def merge_unique_limited(existing: list[str], new_values: list[str], *, limit: int) -> list[str]:
    merged = list(dict.fromkeys([*existing, *[value for value in new_values if value]]))
    return merged[-limit:]


def top_recurring_intents(existing: list[str], new_intents: list[str], *, limit: int) -> list[str]:
    counts = Counter([*existing, *new_intents])
    return [intent for intent, _ in counts.most_common(limit)]
