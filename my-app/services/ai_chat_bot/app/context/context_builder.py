from typing import Any

from app.context.context_optimizer import ContextOptimizer
from app.context.context_ranker import ContextRanker
from app.context.memory_merger import MemoryMerger
from app.context.prompt_builder import PromptBuilder
from app.context.retrieval_merger import RetrievalMerger
from app.context.token_controller import TokenController
from app.core.logger import log_error, log_event
from app.exceptions.context_exceptions import ContextBuilderError
from app.models.context_models import ContextMetadata, FinalContext, MemoryContext, PromptContext, TokenBudget


class ContextBuilder:
    """R9 orchestration layer that builds final AI-ready context before Groq."""

    def __init__(
        self,
        *,
        retrieval_merger: RetrievalMerger | None = None,
        memory_merger: MemoryMerger | None = None,
        ranker: ContextRanker | None = None,
        optimizer: ContextOptimizer | None = None,
        prompt_builder: PromptBuilder | None = None,
        token_controller: TokenController | None = None,
    ) -> None:
        self.token_controller = token_controller or TokenController()
        self.retrieval_merger = retrieval_merger or RetrievalMerger()
        self.memory_merger = memory_merger or MemoryMerger()
        self.ranker = ranker or ContextRanker()
        self.optimizer = optimizer or ContextOptimizer(self.token_controller)
        self.prompt_builder = prompt_builder or PromptBuilder(self.token_controller)

    async def build_context(
        self,
        *,
        user_query: str,
        retrieved_context: list[Any] | None = None,
        short_term_memory: list[Any] | None = None,
        long_term_memory: Any | None = None,
        summarized_memory: list[Any] | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
        model_name: str = "llama-3.3-70b-versatile",
        token_budget: TokenBudget | None = None,
        template_name: str = "enterprise_assistant",
        language_hint: str | None = None,
        role: str = "enterprise_ai_assistant",
        metadata: dict[str, Any] | None = None,
    ) -> FinalContext:
        query = str(user_query or "").strip()
        if not query:
            raise ContextBuilderError("user_query cannot be empty")

        log_event("context_generation_started", user_id=user_id, session_id=session_id, model_name=model_name)
        try:
            budget = token_budget or self.token_controller.build_budget(model_name=model_name)
            prompt_context = await self.merge_context(
                user_query=query,
                retrieved_context=retrieved_context,
                short_term_memory=short_term_memory,
                long_term_memory=long_term_memory,
                summarized_memory=summarized_memory,
                user_id=user_id,
                session_id=session_id,
                language_hint=language_hint,
                model_name=model_name,
                metadata=metadata or {},
            )
            optimized_context, token_usage = await self.optimize_context(prompt_context=prompt_context, budget=budget)
            final_prompt = await self.build_final_prompt(
                prompt_context=optimized_context,
                budget=budget,
                template_name=template_name,
                role=role,
            )
            final = FinalContext(
                user_query=query,
                final_prompt=final_prompt.final_prompt,
                messages=final_prompt.messages,
                retrieved_context=optimized_context.retrieved_context,
                short_term_memory=optimized_context.short_term_memory,
                long_term_memory=optimized_context.long_term_memory,
                summarized_memory=optimized_context.summarized_memory,
                semantic_metadata=optimized_context.metadata,
                token_usage=token_usage | {"prompt_tokens": final_prompt.token_count, "template_name": final_prompt.template_name},
                token_budget=budget,
            )
            log_event("context_generation_completed", prompt_tokens=final.token_usage.get("prompt_tokens", 0))
            return final
        except Exception as exc:
            log_error("Context generation failed", error_type=type(exc).__name__, exc_info=True)
            if isinstance(exc, ContextBuilderError):
                raise
            raise ContextBuilderError("Failed to build final context") from exc

    async def merge_context(
        self,
        *,
        user_query: str,
        retrieved_context: list[Any] | None,
        short_term_memory: list[Any] | None,
        long_term_memory: Any | None,
        summarized_memory: list[Any] | None,
        user_id: str | None,
        session_id: str | None,
        language_hint: str | None,
        model_name: str,
        metadata: dict[str, Any],
    ) -> PromptContext:
        retrieval = await self.retrieval_merger.merge_retrieval(retrieved_context, model_name=model_name)
        short_memory, long_memory, summary_memory = await self.memory_merger.merge_memory(
            short_term_memory=short_term_memory,
            long_term_memory=long_term_memory,
            summarized_memory=summarized_memory,
            model_name=model_name,
        )
        context_metadata = ContextMetadata(
            user_id=user_id,
            session_id=session_id,
            language_hint=language_hint,
            retrieval_count=len(retrieval),
            memory_count=len(short_memory) + len(long_memory) + len(summary_memory),
            hallucination_controls=[
                "duplicate_filtering",
                "score_based_ranking",
                "token_budget_enforcement",
                "grounded_prompt_guardrails",
            ],
            metadata=metadata,
        )
        return PromptContext(
            user_query=user_query,
            retrieved_context=retrieval,
            short_term_memory=short_memory,
            long_term_memory=long_memory,
            summarized_memory=summary_memory,
            metadata=context_metadata,
        )

    async def optimize_context(self, *, prompt_context: PromptContext, budget: TokenBudget) -> tuple[PromptContext, dict]:
        memory_context: list[MemoryContext] = [
            *prompt_context.short_term_memory,
            *prompt_context.long_term_memory,
            *prompt_context.summarized_memory,
        ]
        ranking = await self.ranker.rank_context(
            user_query=prompt_context.user_query,
            retrieved_context=prompt_context.retrieved_context,
            memory_context=memory_context,
        )
        selected_retrieval, selected_memory, token_usage = await self.optimizer.optimize(
            ranked_context=ranking.ranked_context,
            retrieved_context=prompt_context.retrieved_context,
            memory_context=memory_context,
            budget=budget,
        )
        short_ids = {item.context_id for item in prompt_context.short_term_memory}
        long_ids = {item.context_id for item in prompt_context.long_term_memory}
        summary_ids = {item.context_id for item in prompt_context.summarized_memory}
        optimized = PromptContext(
            user_query=prompt_context.user_query,
            retrieved_context=selected_retrieval,
            short_term_memory=[item for item in selected_memory if item.context_id in short_ids],
            long_term_memory=[item for item in selected_memory if item.context_id in long_ids],
            summarized_memory=[item for item in selected_memory if item.context_id in summary_ids],
            metadata=prompt_context.metadata,
        )
        optimized.metadata.selected_retrieval_count = len(optimized.retrieved_context)
        optimized.metadata.selected_memory_count = len(selected_memory)
        optimized.metadata.warnings.extend(
            [
                f"dropped_duplicates={ranking.dropped_duplicates}",
                f"dropped_low_score={ranking.dropped_low_score}",
                f"dropped_for_budget={token_usage.get('dropped_for_budget', 0)}",
            ]
        )
        return optimized, token_usage

    async def build_final_prompt(
        self,
        *,
        prompt_context: PromptContext,
        budget: TokenBudget,
        template_name: str,
        role: str,
    ):
        return await self.prompt_builder.build_prompt(
            prompt_context=prompt_context,
            budget=budget,
            template_name=template_name,
            role=role,
        )

