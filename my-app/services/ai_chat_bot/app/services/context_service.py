from app.memory.context_window import ContextWindowManager
from app.memory.memory_manager import MemoryManager
from app.context.context_builder import ContextBuilder
from app.models.context_models import FinalContext, TokenBudget
from app.models.memory_models import ContextWindow, ConversationMemory
from app.models.message_models import ChatMessage


class ContextService:
    """Application service for AI-ready active conversation context."""

    def __init__(
        self,
        *,
        memory_manager: MemoryManager | None = None,
        context_window_manager: ContextWindowManager | None = None,
        context_builder: ContextBuilder | None = None,
    ) -> None:
        self.memory_manager = memory_manager or MemoryManager()
        self.context_window_manager = context_window_manager or ContextWindowManager()
        self.context_builder = context_builder or ContextBuilder()

    async def get_active_context(self, session_id: str) -> ConversationMemory:
        return await self.memory_manager.get_conversation_memory(session_id)

    async def build_context_window(self, *, session_id: str, user_id: str, messages: list[ChatMessage]) -> ContextWindow:
        return await self.context_window_manager.build_window(session_id=session_id, user_id=user_id, messages=messages)

    async def build_final_context(
        self,
        *,
        user_query: str,
        retrieved_context: list | None = None,
        short_term_memory: list | None = None,
        long_term_memory=None,
        summarized_memory: list | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
        model_name: str = "llama-3.3-70b-versatile",
        token_budget: TokenBudget | None = None,
        template_name: str = "enterprise_assistant",
        language_hint: str | None = None,
        role: str = "enterprise_ai_assistant",
        metadata: dict | None = None,
    ) -> FinalContext:
        return await self.context_builder.build_context(
            user_query=user_query,
            retrieved_context=retrieved_context,
            short_term_memory=short_term_memory,
            long_term_memory=long_term_memory,
            summarized_memory=summarized_memory,
            user_id=user_id,
            session_id=session_id,
            model_name=model_name,
            token_budget=token_budget,
            template_name=template_name,
            language_hint=language_hint,
            role=role,
            metadata=metadata,
        )
