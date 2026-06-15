import pytest

from app.context.context_builder import ContextBuilder
from app.models.context_models import TokenBudget
from app.services.optimization_service import OptimizationService


@pytest.mark.asyncio
@pytest.mark.integration
async def test_optimized_context_generation_can_be_cached(fake_redis, retrieved_chunks, chat_messages):
    service = OptimizationService()
    service.caching_service.cache_manager.redis_client = fake_redis
    service.caching_service.retrieval_cache.cache_manager.redis_client = fake_redis
    await service.cache_retrieval("pricing", [chunk.model_dump() for chunk in retrieved_chunks])

    cached = await service.get_cached_retrieval("pricing")
    context = await ContextBuilder().build_context(
        user_query="pricing",
        retrieved_context=cached.value,
        short_term_memory=chat_messages,
        token_budget=TokenBudget(
            model_name="gpt-4o-mini",
            max_context_tokens=2400,
            reserved_response_tokens=512,
            system_prompt_tokens=400,
        ),
    )

    assert cached.hit is True
    assert context.messages
    assert context.token_usage["prompt_tokens"] <= 1200
