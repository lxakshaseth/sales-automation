import asyncio
import json

import pytest


@pytest.mark.asyncio
@pytest.mark.unit
async def test_session_storage_and_restoration(fake_redis):
    await fake_redis.set("memory:session-1", {"messages": ["hello"]}, ex=60)

    restored = await fake_redis.get("memory:session-1")

    assert json.loads(restored)["messages"] == ["hello"]
    assert await fake_redis.ttl("memory:session-1") > 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_ttl_expiration(fake_redis):
    await fake_redis.set("memory:short", "value", ex=1)
    fake_redis._expires_at["memory:short"] = 0

    assert await fake_redis.get("memory:short") is None
    assert await fake_redis.ttl("memory:short") == -2


@pytest.mark.asyncio
@pytest.mark.unit
async def test_concurrent_session_safety(fake_redis):
    async def write(index: int) -> None:
        await fake_redis.set(f"memory:session:{index}", f"value-{index}", ex=60)

    await asyncio.gather(*(write(index) for index in range(25)))

    assert len(fake_redis._store) == 25

