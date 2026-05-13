import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core import rate_limiter
from app.core.rate_limiter import (
    RateLimitMiddleware,
    check_rate_limit,
    check_tool_rate_limit,
    close_rate_limiter,
    increment_usage,
    reset_limit,
)


class RateLimiterTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.redis = AsyncMock()
        self.redis.pipeline = MagicMock()
        self.redis.ttl.return_value = 60
        self.client_patch = patch.object(rate_limiter, "_get_redis_client", return_value=self.redis)
        self.client_patch.start()
        self.log_patch = patch.object(rate_limiter, "log_event")
        self.log_patch.start()

    async def asyncTearDown(self):
        self.client_patch.stop()
        self.log_patch.stop()
        await close_rate_limiter()

    def _pipeline(self, count: int):
        pipe = MagicMock()
        pipe.incr.return_value = pipe
        pipe.expire.return_value = pipe
        pipe.execute = AsyncMock(return_value=[count, True])
        self.redis.pipeline.return_value = pipe
        return pipe

    async def test_increment_usage_uses_pipeline_and_ttl(self):
        self._pipeline(1)

        result = await increment_usage("user-123", scope="user", limit_type="message")

        self.assertEqual(result["count"], 1)
        self.assertEqual(result["ttl"], 60)
        self.redis.pipeline.assert_called_once()

    async def test_check_rate_limit_allows_with_remaining_quota(self):
        self._pipeline(3)

        result = await check_rate_limit("user-123", scope="user", limit_type="message", limit=10)

        self.assertTrue(result["allowed"])
        self.assertEqual(result["remaining"], 7)

    async def test_check_rate_limit_blocks_when_limit_exceeded(self):
        self._pipeline(11)

        result = await check_rate_limit("user-123", scope="user", limit_type="message", limit=10)

        self.assertFalse(result["allowed"])
        self.assertEqual(result["retry_after"], 60)

    async def test_check_rate_limit_can_inspect_without_increment(self):
        self.redis.get.return_value = "4"

        result = await check_rate_limit("user-123", scope="user", limit_type="message", limit=10, increment=False)

        self.assertTrue(result["allowed"])
        self.assertEqual(result["count"], 4)

    async def test_reset_limit_deletes_key(self):
        self.redis.delete.return_value = 1

        result = await reset_limit("user-123", scope="user", limit_type="message")

        self.assertTrue(result["deleted"])
        self.redis.delete.assert_awaited_once()

    async def test_check_tool_rate_limit_uses_email_limit(self):
        self._pipeline(1)

        result = await check_tool_rate_limit("user-123", "send_email")

        self.assertEqual(result["scope"], "tool")
        self.assertEqual(result["limit_type"], "email")

    async def test_close_rate_limiter_closes_client(self):
        client = AsyncMock()
        rate_limiter._redis_client = client

        await close_rate_limiter()

        client.aclose.assert_awaited_once()
        self.assertIsNone(rate_limiter._redis_client)


class RateLimitMiddlewareTests(unittest.TestCase):
    def test_middleware_allows_request_and_sets_headers(self):
        app = FastAPI()
        app.add_middleware(RateLimitMiddleware)

        @app.get("/ping")
        async def ping():
            return {"ok": True}

        async def allow(*args, **kwargs):
            return {"allowed": True, "limit": 20, "remaining": 19, "reset_in": 60, "retry_after": 0}

        with patch.object(rate_limiter, "check_rate_limit", new=AsyncMock(side_effect=allow)):
            response = TestClient(app).get("/ping", headers={"x-user-id": "user-123"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["x-ratelimit-limit"], "20")

    def test_middleware_blocks_limited_request(self):
        app = FastAPI()
        app.add_middleware(RateLimitMiddleware)

        @app.get("/ping")
        async def ping():
            return {"ok": True}

        async def block(*args, **kwargs):
            return {"allowed": False, "limit": 20, "remaining": 0, "reset_in": 60, "retry_after": 60}

        with patch.object(rate_limiter, "check_rate_limit", new=AsyncMock(side_effect=block)):
            response = TestClient(app).get("/ping")

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["error"], "rate limit exceeded")


if __name__ == "__main__":
    unittest.main()
