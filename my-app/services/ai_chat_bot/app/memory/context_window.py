from app.core.logger import log_event
from app.models.memory_models import ContextWindow, MemoryConfig
from app.models.message_models import ChatMessage
from app.utils.context_helpers import estimate_message_tokens


class ContextWindowManager:
    """Build rolling token-aware message windows, prioritizing latest turns."""

    def __init__(self, config: MemoryConfig | None = None) -> None:
        self.config = config or MemoryConfig()

    async def build_window(
        self,
        *,
        session_id: str,
        user_id: str,
        messages: list[ChatMessage],
    ) -> ContextWindow:
        selected: list[ChatMessage] = []
        total_tokens = 0

        for message in reversed(messages):
            token_count = message.token_count or estimate_message_tokens(message.message_text)
            if len(selected) >= self.config.max_messages:
                break
            if selected and total_tokens + token_count > self.config.token_limit:
                break
            selected.append(message.model_copy(update={"token_count": token_count}))
            total_tokens += token_count

        selected.reverse()
        trimmed_count = max(0, len(messages) - len(selected))
        log_event(
            "short_term_context_window_built",
            session_id=session_id,
            user_id=user_id,
            message_count=len(selected),
            token_count=total_tokens,
            trimmed_count=trimmed_count,
        )
        return ContextWindow(
            session_id=session_id,
            user_id=user_id,
            messages=selected,
            token_count=total_tokens,
            max_messages=self.config.max_messages,
            token_limit=self.config.token_limit,
            trimmed_count=trimmed_count,
        )
