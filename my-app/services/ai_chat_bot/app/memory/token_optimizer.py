from app.core.logger import log_event
from app.models.compression_models import TokenUsage
from app.models.message_models import ChatMessage
from app.models.summary_models import SummarizationConfig
from app.utils.token_helpers import estimate_tokens, trim_text_to_token_limit


class TokenOptimizer:
    """Model-agnostic token estimation and overflow prevention."""

    def estimate_text_tokens(self, text: str, *, model_name: str | None = None) -> int:
        return estimate_tokens(text, model_name=model_name)

    def estimate_messages_tokens(self, messages: list[ChatMessage], *, model_name: str | None = None) -> int:
        return sum(estimate_tokens(f"{message.role}: {message.message_text}", model_name=model_name) for message in messages)

    def trim_to_budget(self, text: str, config: SummarizationConfig) -> str:
        trimmed = trim_text_to_token_limit(text, config.max_input_tokens, model_name=config.model_name)
        if len(trimmed) < len(str(text or "")):
            log_event("memory_token_overflow_prevented", max_input_tokens=config.max_input_tokens)
        return trimmed

    def usage(self, *, input_text: str, output_text: str, config: SummarizationConfig) -> TokenUsage:
        input_tokens = self.estimate_text_tokens(input_text, model_name=config.model_name)
        output_tokens = self.estimate_text_tokens(output_text, model_name=config.model_name)
        saved = max(0, input_tokens - output_tokens)
        ratio = round(output_tokens / input_tokens, 4) if input_tokens else 0.0
        log_event("memory_token_usage_estimated", input_tokens=input_tokens, output_tokens=output_tokens, saved_tokens=saved)
        return TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            saved_tokens=saved,
            compression_ratio=ratio,
            model_name=config.model_name,
        )
