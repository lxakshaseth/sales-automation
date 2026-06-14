import time

import pytest

from app.context.context_builder import ContextBuilder


@pytest.mark.asyncio
@pytest.mark.performance
async def test_context_builder_latency_budget(retrieved_chunks, chat_messages, small_token_budget):
    started = time.perf_counter()

    result = await ContextBuilder().build_context(
        user_query="WhatsApp pricing follow-up",
        retrieved_context=retrieved_chunks,
        short_term_memory=chat_messages,
        token_budget=small_token_budget,
    )

    duration_ms = (time.perf_counter() - started) * 1000
    assert result.final_prompt
    assert duration_ms < 1500


@pytest.mark.asyncio
@pytest.mark.performance
async def test_cache_hit_latency_budget(fake_redis):
    from app.optimization.cache_manager import CacheManager

    cache = CacheManager(redis_client=fake_redis)
    await cache.cache_retrieval("pricing", [{"chunk_id": "c1"}])
    started = time.perf_counter()

    result = await cache.fetch_cached_retrieval("pricing")

    duration_ms = (time.perf_counter() - started) * 1000
    assert result.hit is True
    assert duration_ms < 50

