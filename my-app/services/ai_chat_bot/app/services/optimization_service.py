from app.context.context_optimizer import ContextOptimizer
from app.memory.memory_cleanup import MemoryCleanup
from app.memory.memory_optimizer import MemoryOptimizer
from app.models.batch_models import BatchRequest, BatchResult
from app.models.cache_models import CacheResult
from app.models.context_models import MemoryContext, RetrievalContext, TokenBudget
from app.models.message_models import ChatMessage
from app.models.optimization_models import MemoryCleanupResult, MemoryOptimizationResult, OptimizationConfig, OptimizationResult
from app.models.ranking_models import RankedContext
from app.models.summary_models import ConversationSummary, SummarizationConfig
from app.optimization.request_coordinator import RequestCoordinator
from app.optimization.token_optimizer import ProductionTokenOptimizer
from app.services.async_execution_service import AsyncExecutionService
from app.services.batching_service import BatchingService
from app.services.caching_service import CachingService


class OptimizationService:
    """Internal service facade for memory, context, and R10 production optimization."""

    def __init__(
        self,
        *,
        optimizer: MemoryOptimizer | None = None,
        cleanup: MemoryCleanup | None = None,
        context_optimizer: ContextOptimizer | None = None,
        config: OptimizationConfig | None = None,
        caching_service: CachingService | None = None,
        batching_service: BatchingService | None = None,
        async_execution_service: AsyncExecutionService | None = None,
        request_coordinator: RequestCoordinator | None = None,
        token_optimizer: ProductionTokenOptimizer | None = None,
    ) -> None:
        self.optimizer = optimizer or MemoryOptimizer()
        self.cleanup = cleanup or MemoryCleanup()
        self.context_optimizer = context_optimizer or ContextOptimizer()
        self.config = config or OptimizationConfig()
        self.caching_service = caching_service or CachingService()
        self.batching_service = batching_service or BatchingService()
        self.async_execution_service = async_execution_service or AsyncExecutionService()
        self.request_coordinator = request_coordinator or RequestCoordinator(config=self.config)
        self.token_optimizer = token_optimizer or ProductionTokenOptimizer()

    async def optimize_long_conversation(
        self,
        *,
        user_id: str,
        session_id: str | None,
        messages: list[ChatMessage],
        config: SummarizationConfig | None = None,
    ) -> MemoryOptimizationResult:
        return await self.optimizer.optimize_long_conversation(
            user_id=user_id,
            session_id=session_id,
            messages=messages,
            config=config,
        )

    async def cleanup_summaries(self, summaries: list[ConversationSummary], *, keep_latest: int = 20) -> MemoryCleanupResult:
        return await self.cleanup.cleanup_redundant_summaries(summaries, keep_latest=keep_latest)

    async def optimize_context(
        self,
        *,
        ranked_context: list[RankedContext],
        retrieved_context: list[RetrievalContext],
        memory_context: list[MemoryContext],
        token_budget: TokenBudget,
    ) -> tuple[list[RetrievalContext], list[MemoryContext], dict]:
        return await self.context_optimizer.optimize(
            ranked_context=ranked_context,
            retrieved_context=retrieved_context,
            memory_context=memory_context,
            budget=token_budget,
        )

    async def get_cached_retrieval(self, query: str, *, metadata_filter: dict | None = None) -> CacheResult:
        return await self.caching_service.get_retrieval(query, metadata_filter=metadata_filter)

    async def cache_retrieval(self, query: str, results, *, metadata_filter: dict | None = None) -> CacheResult:
        return await self.caching_service.set_retrieval(query, results, metadata_filter=metadata_filter)

    async def get_cached_embedding(self, text: str, *, model_name: str | None = None) -> CacheResult:
        return await self.caching_service.get_embedding(text, model_name=model_name)

    async def cache_embedding(self, text: str, embedding: list[float], *, model_name: str | None = None) -> CacheResult:
        return await self.caching_service.set_embedding(text, embedding, model_name=model_name)

    async def process_batch(self, request: BatchRequest, handler) -> BatchResult:
        return await self.batching_service.process_batch(request, handler)

    async def run_optimized_request(self, operation_name: str, operation) -> OptimizationResult:
        return await self.request_coordinator.coordinate(operation_name, operation)

    async def optimize_prompt_tokens(self, text: str, *, token_limit: int | None = None, model_name: str | None = None):
        return await self.token_optimizer.optimize_text(
            text,
            token_limit=token_limit or self.config.token_budget,
            model_name=model_name,
        )
