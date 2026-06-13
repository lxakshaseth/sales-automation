from app.context.token_controller import TokenController
from app.core.logger import log_event
from app.exceptions.optimization_exceptions import OptimizationTokenError
from app.models.optimization_models import TokenUsage


class ProductionTokenOptimizer:
    """Cost-focused token optimization for prompts and context payloads."""

    def __init__(self, *, token_controller: TokenController | None = None) -> None:
        self.token_controller = token_controller or TokenController()

    async def optimize_text(self, text: str, *, token_limit: int, model_name: str | None = None) -> tuple[str, TokenUsage]:
        original_tokens = self.token_controller.estimate_text(text, model_name=model_name)
        if token_limit <= 0:
            raise OptimizationTokenError("token_limit must be positive")
        optimized = self.token_controller.trim_text(text, token_limit, model_name=model_name)
        optimized_tokens = self.token_controller.estimate_text(optimized, model_name=model_name)
        usage = TokenUsage(
            prompt_tokens=optimized_tokens,
            total_tokens=optimized_tokens,
            saved_tokens=max(0, original_tokens - optimized_tokens),
            model_name=model_name,
        )
        log_event("optimization_token_completed", original_tokens=original_tokens, optimized_tokens=optimized_tokens, saved_tokens=usage.saved_tokens)
        return optimized, usage

