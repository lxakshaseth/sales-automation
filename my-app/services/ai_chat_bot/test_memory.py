import unittest
from unittest.mock import AsyncMock, patch

from redis.exceptions import RedisError

from app.core.config import REDIS_MEMORY_TTL_SECONDS
from app.tools import memory_tool
from app.tools.memory_tool import (
    MemoryStoreError,
    append_memory,
    clear_memory,
    get_memory,
    save_memory,
)


class MemoryToolTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.redis = AsyncMock()
        self.client_patch = patch.object(memory_tool, "_get_redis_client", return_value=self.redis)
        self.client_patch.start()

    def tearDown(self):
        self.client_patch.stop()

    async def test_save_memory_stores_json_list_with_ttl(self):
        result = await save_memory("user-123", {"role": "user", "content": "Hello"})

        self.assertEqual(result, [{"role": "user", "content": "Hello"}])
        self.redis.set.assert_awaited_once_with(
            "agent:memory:user-123",
            '[{"role": "user", "content": "Hello"}]',
            ex=REDIS_MEMORY_TTL_SECONDS,
        )

    async def test_get_memory_returns_empty_list_when_missing(self):
        self.redis.get.return_value = None

        result = await get_memory("user-123")

        self.assertEqual(result, [])

    async def test_get_memory_deserializes_json_list(self):
        self.redis.get.return_value = '[{"role": "assistant", "content": "Hi"}]'

        result = await get_memory("user-123")

        self.assertEqual(result, [{"role": "assistant", "content": "Hi"}])

    async def test_append_memory_refreshes_ttl(self):
        self.redis.get.return_value = '[{"role": "user", "content": "Hello"}]'

        result = await append_memory("user-123", {"role": "assistant", "content": "Hi"})

        self.assertEqual(
            result,
            [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi"},
            ],
        )
        self.redis.set.assert_awaited_once_with(
            "agent:memory:user-123",
            '[{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}]',
            ex=REDIS_MEMORY_TTL_SECONDS,
        )

    async def test_clear_memory_returns_true_when_deleted(self):
        self.redis.delete.return_value = 1

        result = await clear_memory("user-123")

        self.assertTrue(result)
        self.redis.delete.assert_awaited_once_with("agent:memory:user-123")

    async def test_redis_errors_are_wrapped(self):
        self.redis.get.side_effect = RedisError("connection failed")

        with patch.object(memory_tool.logger, "exception"), self.assertRaises(MemoryStoreError):
            await get_memory("user-123")


if __name__ == "__main__":
    unittest.main()
