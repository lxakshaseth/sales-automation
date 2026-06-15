import asyncio

import pytest

from app.models.batch_models import BatchRequest
from app.optimization.cache_manager import CacheManager
from app.optimization.concurrency_manager import ConcurrencyManager
from app.services.optimization_service import OptimizationService


@pytest.mark.asyncio
@pytest.mark.unit
async def test_retrieval_and_embedding_cache_hit(fake_redis):
    cache = CacheManager(redis_client=fake_redis)
    service = OptimizationService()
    service.caching_service.cache_manager = cache
    service.caching_service.retrieval_cache.cache_manager = cache
    service.caching_service.embedding_cache.cache_manager = cache

    await service.cache_retrieval("नमस्ते pricing", [{"chunk_id": "c1"}])
    retrieval = await service.get_cached_retrieval("नमस्ते pricing")
    await service.cache_embedding("hello", [0.1, 0.2], model_name="fake")
    embedding = await service.get_cached_embedding("hello", model_name="fake")

    assert retrieval.hit is True
    assert embedding.hit is True
    assert embedding.value == [0.1, 0.2]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_batch_processing_success():
    service = OptimizationService()

    async def handler(value: int) -> int:
        return value * 10

    result = await service.process_batch(BatchRequest(batch_type="generic", items=[1, 2, 3], batch_size=2), handler)

    assert result.success is True
    assert result.successful_items == 3
    assert [item.value for item in result.results] == [10, 20, 30]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_batch_processing_captures_item_failures():
    service = OptimizationService()

    async def handler(value: int) -> int:
        if value == 2:
            raise RuntimeError("boom")
        return value

    result = await service.process_batch(BatchRequest(batch_type="generic", items=[1, 2, 3]), handler)

    assert result.success is False
    assert result.failed_items == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_concurrency_manager_caps_parallel_execution():
    manager = ConcurrencyManager(max_concurrency=2)
    observed: list[int] = []

    async def work() -> int:
        observed.append(manager.active_requests)
        await asyncio.sleep(0.01)
        return manager.active_requests

    await asyncio.gather(*(manager.run("test", work()) for _ in range(5)))

    assert max(observed) <= 2


@pytest.mark.asyncio
@pytest.mark.unit
async def test_token_optimizer_reduces_prompt_size():
    service = OptimizationService()
    optimized, usage = await service.optimize_prompt_tokens("word " * 100, token_limit=20, model_name="gpt-4o-mini")

    assert usage.prompt_tokens <= 20
    assert usage.saved_tokens > 0
    assert optimized.strip()

