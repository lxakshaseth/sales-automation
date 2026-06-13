from app.context.token_controller import TokenController
from app.core.logger import log_event
from app.models.context_models import MemoryContext, RetrievalContext, TokenBudget
from app.models.ranking_models import RankedContext


class ContextOptimizer:
    """Select the highest-quality context that fits inside the token budget."""

    def __init__(self, token_controller: TokenController | None = None) -> None:
        self.token_controller = token_controller or TokenController()

    async def optimize(
        self,
        *,
        ranked_context: list[RankedContext],
        retrieved_context: list[RetrievalContext],
        memory_context: list[MemoryContext],
        budget: TokenBudget,
    ) -> tuple[list[RetrievalContext], list[MemoryContext], dict]:
        log_event("context_token_optimization_started", ranked_count=len(ranked_context), budget=budget.available_context_tokens)
        by_retrieval_id = {item.context_id: item for item in retrieved_context}
        by_memory_id = {item.context_id: item for item in memory_context}
        selected_retrieval: list[RetrievalContext] = []
        selected_memory: list[MemoryContext] = []
        used_tokens = 0
        dropped_for_budget = 0

        for ranked in ranked_context:
            item_tokens = ranked.token_count or self.token_controller.estimate_text(ranked.content, model_name=budget.model_name)
            if used_tokens + item_tokens > budget.available_context_tokens:
                dropped_for_budget += 1
                continue
            if ranked.source == "retrieval" and ranked.context_id in by_retrieval_id:
                selected_retrieval.append(by_retrieval_id[ranked.context_id])
            elif ranked.context_id in by_memory_id:
                selected_memory.append(by_memory_id[ranked.context_id])
            used_tokens += item_tokens

        token_usage = {
            "context_tokens": used_tokens,
            "available_context_tokens": budget.available_context_tokens,
            "max_context_tokens": budget.max_context_tokens,
            "reserved_response_tokens": budget.reserved_response_tokens,
            "dropped_for_budget": dropped_for_budget,
            "model_name": budget.model_name,
        }
        log_event("context_token_optimization_completed", **token_usage)
        return selected_retrieval, selected_memory, token_usage

