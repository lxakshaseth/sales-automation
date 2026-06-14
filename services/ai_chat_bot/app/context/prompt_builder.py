from app.context.prompt_templates import get_prompt_template
from app.context.token_controller import TokenController
from app.core.logger import log_error, log_event
from app.exceptions.context_exceptions import PromptConstructionError, TokenBudgetExceededError
from app.models.context_models import MemoryContext, PromptContext, TokenBudget
from app.models.prompt_models import PromptBuildResult
from app.utils.prompt_helpers import compact_lines, format_context_block


class PromptBuilder:
    """Build role-aware, token-aware prompts for the Groq LLM boundary."""

    def __init__(self, token_controller: TokenController | None = None) -> None:
        self.token_controller = token_controller or TokenController()

    async def build_prompt(
        self,
        *,
        prompt_context: PromptContext,
        budget: TokenBudget,
        template_name: str = "enterprise_assistant",
        role: str = "enterprise_ai_assistant",
    ) -> PromptBuildResult:
        log_event("context_prompt_construction_started", template_name=template_name, role=role)
        try:
            template = get_prompt_template(template_name)
            context_text = self._render_context(prompt_context)
            system_content = compact_lines(
                [
                    template.system_template,
                    "Guardrails:",
                    *[f"- {guardrail}" for guardrail in template.guardrails],
                    f"Assistant role: {role}",
                    f"Language hint: {prompt_context.metadata.language_hint or 'auto'}",
                ]
            )
            user_content = template.user_template.format(context=context_text, query=prompt_context.user_query)
            messages = [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content},
            ]
            token_count = self.token_controller.estimate_messages(messages, model_name=budget.model_name)
            if self.token_controller.check_overflow(token_count + budget.reserved_response_tokens, budget):
                raise TokenBudgetExceededError("final prompt exceeds model context window")

            final_prompt = f"{system_content}\n\n{user_content}"
            log_event("context_prompt_construction_completed", token_count=token_count, template_name=template.name)
            return PromptBuildResult(
                final_prompt=final_prompt,
                messages=messages,
                template_name=template.name,
                token_count=token_count,
                metadata={"mode": template.mode, "role": role},
            )
        except TokenBudgetExceededError:
            raise
        except Exception as exc:
            log_error("Prompt construction failed", error_type=type(exc).__name__, exc_info=True)
            raise PromptConstructionError("Failed to construct final prompt") from exc

    def _render_context(self, prompt_context: PromptContext) -> str:
        retrieval_lines = [
            f"[RAG:{index}] score={item.score:.2f} source={item.source_name or item.document_id or 'unknown'} :: {item.content}"
            for index, item in enumerate(prompt_context.retrieved_context, start=1)
        ]
        short_memory = self._memory_lines(prompt_context.short_term_memory, "STM")
        long_memory = self._memory_lines(prompt_context.long_term_memory, "LTM")
        summaries = self._memory_lines(prompt_context.summarized_memory, "SUMMARY")
        return compact_lines(
            [
                "Final AI Context",
                format_context_block("Retrieved RAG chunks", retrieval_lines),
                format_context_block("Recent short-term memory", short_memory),
                format_context_block("Long-term memory", long_memory),
                format_context_block("Summarized memory", summaries),
                "Instruction: Ground the answer in the highest-ranked context. When the answer is not supported, state the gap.",
            ]
        )

    def _memory_lines(self, memories: list[MemoryContext], label: str) -> list[str]:
        return [
            f"[{label}:{index}] importance={item.importance:.2f} confidence={item.confidence:.2f} :: {item.content}"
            for index, item in enumerate(memories, start=1)
        ]

