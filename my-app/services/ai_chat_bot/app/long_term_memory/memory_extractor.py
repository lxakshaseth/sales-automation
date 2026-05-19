from app.models.long_term_memory_models import MemoryInsight, UserPreference
from app.utils.long_term_memory_helpers import extract_lightweight_insights, extract_lightweight_preferences


class MemoryExtractor:
    """
    Lightweight extraction layer.

    R7 does not call an LLM directly; future versions can replace this with a
    Groq-powered extraction prompt while preserving the same return types.
    """

    async def extract_preferences(self, *, user_id: str, text: str) -> dict[str, UserPreference]:
        return extract_lightweight_preferences(user_id, text)

    async def extract_insights(self, *, user_id: str, text: str, session_id: str | None = None) -> list[MemoryInsight]:
        return extract_lightweight_insights(user_id, text, session_id=session_id)
