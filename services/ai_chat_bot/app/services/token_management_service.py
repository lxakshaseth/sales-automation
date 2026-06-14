from app.memory.token_optimizer import TokenOptimizer
from app.models.compression_models import TokenUsage
from app.models.message_models import ChatMessage
from app.models.summary_models import SummarizationConfig


class TokenManagementService:
    """Internal token monitoring and overflow prevention service."""

    def __init__(self, *, token_optimizer: TokenOptimizer | None = None) -> None:
        self.token_optimizer = token_optimizer or TokenOptimizer()

    def estimate_messages(self, messages: list[ChatMessage], *, model_name: str | None = None) -> int:
        return self.token_optimizer.estimate_messages_tokens(messages, model_name=model_name)

    def estimate_text(self, text: str, *, model_name: str | None = None) -> int:
        return self.token_optimizer.estimate_text_tokens(text, model_name=model_name)

    def trim_text(self, text: str, config: SummarizationConfig) -> str:
        return self.token_optimizer.trim_to_budget(text, config)

    def token_usage(self, *, input_text: str, output_text: str, config: SummarizationConfig) -> TokenUsage:
        return self.token_optimizer.usage(input_text=input_text, output_text=output_text, config=config)
