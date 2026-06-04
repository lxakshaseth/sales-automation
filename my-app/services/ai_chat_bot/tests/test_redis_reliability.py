import pytest

from app.core import redis_utils
from app.core.redis_utils import RedisUnavailableError, redis_call
from app.services import conversation_service
from app.tools.memory_tool import MemoryStoreError


@pytest.mark.asyncio
async def test_redis_call_recovers_after_timeout(monkeypatch):
    monkeypatch.setattr(redis_utils, "REDIS_RETRY_ATTEMPTS", 3)
    monkeypatch.setattr(redis_utils, "REDIS_RETRY_BACKOFF_SECONDS", (0, 0, 0))
    calls = {"count": 0}

    async def flaky_operation():
        calls["count"] += 1
        if calls["count"] < 3:
            raise TimeoutError("slow redis")
        return "ok"

    result = await redis_call("test_flaky", flaky_operation, timeout_seconds=1)

    assert result == "ok"
    assert calls["count"] == 3


@pytest.mark.asyncio
async def test_redis_call_raises_after_retries(monkeypatch):
    monkeypatch.setattr(redis_utils, "REDIS_RETRY_ATTEMPTS", 2)
    monkeypatch.setattr(redis_utils, "REDIS_RETRY_BACKOFF_SECONDS", (0, 0))

    async def failing_operation():
        raise TimeoutError("slow redis")

    with pytest.raises(RedisUnavailableError):
        await redis_call("test_timeout", failing_operation, timeout_seconds=1)


@pytest.mark.asyncio
async def test_conversation_memory_falls_back_locally(monkeypatch):
    async def failing_append(_user_id, _message):
        raise MemoryStoreError("redis unavailable")

    monkeypatch.setattr(conversation_service, "append_memory", failing_append)
    conversation_service._local_memory_fallback.clear()

    history = await conversation_service.record_assistant_message("whatsapp:+15550000000", "Hello")

    assert history[-1]["role"] == "assistant"
    assert conversation_service._local_memory_fallback["whatsapp:+15550000000"][-1]["content"] == "Hello"
