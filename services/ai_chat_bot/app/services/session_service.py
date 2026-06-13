from app.memory.session_manager import SessionManager
from app.models.session_models import SessionMetadata, SessionState


class SessionService:
    """Application service for active short-term memory sessions."""

    def __init__(self, *, session_manager: SessionManager | None = None) -> None:
        self.session_manager = session_manager or SessionManager()

    async def create_session(self, user_id: str, metadata: SessionMetadata | None = None) -> SessionState:
        return await self.session_manager.create_session(user_id, metadata)

    async def get_session(self, session_id: str) -> SessionState:
        return await self.session_manager.get_session(session_id)

    async def close_session(self, session_id: str) -> bool:
        return await self.session_manager.close_session(session_id)
