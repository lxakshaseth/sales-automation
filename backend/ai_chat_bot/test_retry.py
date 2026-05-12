import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from app.core import retry_handler
from app.core.retry_handler import RetryExhaustedError, recover_failed_tasks, retry_async, retry_sync


class RetryHandlerTests(unittest.IsolatedAsyncioTestCase):
    async def test_retry_async_succeeds_after_transient_failure(self):
        calls = {"count": 0}

        @retry_async(max_attempts=3, base_delay_seconds=0, jitter_seconds=0, timeout_seconds=1)
        async def flaky():
            calls["count"] += 1
            if calls["count"] < 2:
                raise ConnectionError("temporary")
            return "ok"

        with (
            patch.object(retry_handler.asyncio, "sleep", new=AsyncMock()),
            patch.object(retry_handler.logger, "warning"),
        ):
            result = await flaky()

        self.assertEqual(result, "ok")
        self.assertEqual(calls["count"], 2)

    async def test_retry_async_raises_after_max_attempts(self):
        @retry_async(max_attempts=2, base_delay_seconds=0, jitter_seconds=0, timeout_seconds=1)
        async def always_fails():
            raise ConnectionError("down")

        with (
            patch.object(retry_handler.asyncio, "sleep", new=AsyncMock()),
            patch.object(retry_handler.logger, "warning"),
            patch.object(retry_handler.logger, "exception"),
        ):
            with self.assertRaises(RetryExhaustedError):
                await always_fails()

    async def test_retry_async_timeout_is_retried(self):
        @retry_async(max_attempts=1, base_delay_seconds=0, jitter_seconds=0, timeout_seconds=0.01)
        async def too_slow():
            await asyncio.sleep(0.1)

        with patch.object(retry_handler.logger, "exception"):
            with self.assertRaises(RetryExhaustedError):
                await too_slow()

    async def test_retry_async_can_trigger_failed_task_recovery(self):
        @retry_async(max_attempts=1, base_delay_seconds=0, jitter_seconds=0, recover_failed_tasks=True)
        async def fails():
            raise RuntimeError("failed")

        with (
            patch.object(retry_handler, "_recover_failed_queue_jobs", new=AsyncMock(return_value={"success": True})) as recover,
            patch.object(retry_handler.logger, "exception"),
        ):
            with self.assertRaises(RetryExhaustedError):
                await fails()

        recover.assert_awaited_once()

    async def test_retry_sync_succeeds_after_transient_failure(self):
        calls = {"count": 0}

        @retry_sync(max_attempts=3, base_delay_seconds=0, jitter_seconds=0, timeout_seconds=1)
        def flaky():
            calls["count"] += 1
            if calls["count"] < 2:
                raise TimeoutError("temporary")
            return "ok"

        with (
            patch.object(retry_handler.time, "sleep"),
            patch.object(retry_handler.logger, "warning"),
        ):
            result = flaky()

        self.assertEqual(result, "ok")
        self.assertEqual(calls["count"], 2)

    async def test_retry_sync_raises_after_max_attempts(self):
        @retry_sync(max_attempts=2, base_delay_seconds=0, jitter_seconds=0, timeout_seconds=1)
        def always_fails():
            raise RuntimeError("nope")

        with (
            patch.object(retry_handler.time, "sleep"),
            patch.object(retry_handler.logger, "warning"),
            patch.object(retry_handler.logger, "exception"),
        ):
            with self.assertRaises(RetryExhaustedError):
                always_fails()

    async def test_recover_failed_tasks_delegates_to_queue(self):
        with patch.object(retry_handler, "_recover_failed_queue_jobs", new=AsyncMock(return_value={"success": True})) as recover:
            result = await recover_failed_tasks("agent_tasks")

        self.assertTrue(result["success"])
        recover.assert_awaited_once_with("agent_tasks")


if __name__ == "__main__":
    unittest.main()
