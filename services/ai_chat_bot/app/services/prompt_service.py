from app.context.prompt_builder import PromptBuilder
from app.models.context_models import PromptContext, TokenBudget
from app.models.prompt_models import PromptBuildResult


class PromptService:
    """Service facade for reusable R9 prompt generation."""

    def __init__(self, *, prompt_builder: PromptBuilder | None = None) -> None:
        self.prompt_builder = prompt_builder or PromptBuilder()

    async def build_prompt(
        self,
        *,
        prompt_context: PromptContext,
        token_budget: TokenBudget,
        template_name: str = "enterprise_assistant",
        role: str = "enterprise_ai_assistant",
    ) -> PromptBuildResult:
        return await self.prompt_builder.build_prompt(
            prompt_context=prompt_context,
            budget=token_budget,
            template_name=template_name,
            role=role,
        )

