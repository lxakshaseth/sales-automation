from app.core.logger import log_event
from app.models.context_models import TokenBudget
from app.utils.token_helpers import estimate_messages_tokens, estimate_tokens, trim_text_to_token_limit

GROQ_CONTEXT_LIMITS = {
    "llama-3.3-70b-versatile": 131072,
    "llama-3.1-8b-instant": 131072,
    "mixtral-8x7b-32768": 32768,
    "gemma2-9b-it": 8192,
}

OPENAI_CONTEXT_LIMITS = {
    "gpt-4o-mini": 128000,
    "gpt-4o": 128000,
}


class TokenController:
    """Token estimation and overflow prevention for final LLM context."""

    def resolve_model_limit(self, model_name: str) -> int:
        return GROQ_CONTEXT_LIMITS.get(model_name) or OPENAI_CONTEXT_LIMITS.get(model_name) or 8192

    def build_budget(
        self,
        *,
        model_name: str = "llama-3.3-70b-versatile",
        max_context_tokens: int | None = None,
        reserved_response_tokens: int = 1024,
    ) -> TokenBudget:
        resolved_limit = max_context_tokens or self.resolve_model_limit(model_name)
        return TokenBudget(
            model_name=model_name,
            max_context_tokens=resolved_limit,
            reserved_response_tokens=reserved_response_tokens,
        )

    def estimate_text(self, text: str, *, model_name: str | None = None) -> int:
        return estimate_tokens(text, model_name=model_name)

    def estimate_messages(self, messages: list[dict[str, str]], *, model_name: str | None = None) -> int:
        return estimate_messages_tokens(messages, model_name=model_name)

    def trim_text(self, text: str, token_limit: int, *, model_name: str | None = None) -> str:
        if token_limit <= 0:
            return ""
        return trim_text_to_token_limit(text, token_limit, model_name=model_name)

    def check_overflow(self, token_count: int, budget: TokenBudget) -> bool:
        overflow = token_count > budget.max_context_tokens
        if overflow:
            log_event(
                "context_overflow_prevention",
                token_count=token_count,
                max_context_tokens=budget.max_context_tokens,
                model_name=budget.model_name,
            )
        return overflow

