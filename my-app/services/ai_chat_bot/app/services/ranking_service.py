from app.context.context_ranker import ContextRanker
from app.models.context_models import MemoryContext, RetrievalContext
from app.models.ranking_models import RankingResult


class RankingService:
    """Service facade for R9 semantic context ranking."""

    def __init__(self, *, ranker: ContextRanker | None = None) -> None:
        self.ranker = ranker or ContextRanker()

    async def rank_context(
        self,
        *,
        user_query: str,
        retrieved_context: list[RetrievalContext],
        memory_context: list[MemoryContext],
    ) -> RankingResult:
        return await self.ranker.rank_context(
            user_query=user_query,
            retrieved_context=retrieved_context,
            memory_context=memory_context,
        )

