import re
from abc import ABC, abstractmethod

from app.intelligence.personas.models import ChannelProfile, PersonaProfile


class BasePersona(ABC):
    profile: PersonaProfile

    @abstractmethod
    def apply(self, verified_response: str, *, channel_profile: ChannelProfile) -> str:
        """Apply presentation style without changing verified facts."""

    def _normalize(self, text: str) -> str:
        return re.sub(r"\s+", " ", str(text or "").strip())

    def _truncate(self, text: str, max_chars: int | None) -> str:
        value = text.strip()
        if not max_chars or len(value) <= max_chars:
            return value
        return value[: max(0, max_chars - 3)].rstrip() + "..."

    def _bulletize(self, text: str) -> str:
        parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part.strip()]
        if len(parts) <= 1:
            return text.strip()
        return "\n".join(f"- {part}" for part in parts)
