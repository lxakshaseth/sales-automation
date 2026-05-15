from datetime import datetime, timedelta, timezone

from app.models.memory_models import MemoryConfig


class TTLManager:
    """Centralizes active session TTL decisions."""

    def __init__(self, config: MemoryConfig | None = None) -> None:
        self.config = config or MemoryConfig()

    @property
    def session_ttl_seconds(self) -> int:
        return self.config.session_ttl_seconds

    def expires_at(self) -> datetime:
        return datetime.now(timezone.utc) + timedelta(seconds=self.session_ttl_seconds)
