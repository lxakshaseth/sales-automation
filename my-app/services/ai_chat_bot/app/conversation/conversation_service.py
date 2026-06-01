from app.conversation.conversation_manager import ConversationManager
from app.conversation.models import ConversationResult, ConversationState


class ConversationService:
    """Stateful conversation facade used after security request validation."""

    def __init__(self, manager: ConversationManager | None = None) -> None:
        self.manager = manager or ConversationManager()
        self._states: dict[str, ConversationState] = {}

    def handle_message(
        self,
        *,
        message: str,
        tenant_id: str,
        user_id: str | None,
        session_id: str | None = None,
        preferred_language: str | None = None,
        conversation_history: list[dict[str, object]] | None = None,
    ) -> ConversationResult:
        key = self._key(tenant_id, user_id, session_id)
        state = self._states.setdefault(key, ConversationState(tenant_id=tenant_id, user_id=user_id or session_id or "anonymous"))
        self._hydrate_state_from_history(state, conversation_history or [])
        if preferred_language:
            state.preferred_language = preferred_language
        result = self.manager.handle(message, state)
        return result

    def get_state(self, *, tenant_id: str, user_id: str | None, session_id: str | None = None) -> ConversationState:
        return self._states[self._key(tenant_id, user_id, session_id)]

    def _key(self, tenant_id: str, user_id: str | None, session_id: str | None = None) -> str:
        return f"{tenant_id}:{user_id or session_id or 'anonymous'}"

    def _hydrate_state_from_history(self, state: ConversationState, history: list[dict[str, object]]) -> None:
        if not history or state.lead.industry:
            return
        for item in history[-20:]:
            if str(item.get("role") or "").lower() != "user":
                continue
            content = str(item.get("content") or item.get("message") or "").strip()
            if not content:
                continue
            intent = self.manager.intent_detector.detect(content)
            self.manager.lead_qualifier.update(state, content, intent.intent)
