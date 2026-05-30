import unittest
from unittest.mock import AsyncMock, patch

from app.core import event_bus, retry_handler
from app.core.event_bus import (
    EVENT_APPOINTMENT_BOOKED,
    EVENT_LEAD_SAVED,
    EVENT_MESSAGE_RECEIVED,
    close_event_bus,
    emit_event,
    handle_event,
    subscribe_event,
)
from app.core.retry_handler import RetryConfig


class EventBusTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.original_handlers = {key: list(value) for key, value in event_bus._handlers.items()}
        event_bus._handlers.clear()

    async def asyncTearDown(self):
        event_bus._handlers.clear()
        event_bus._handlers.update({key: list(value) for key, value in self.original_handlers.items()})
        await close_event_bus()

    async def test_subscribe_and_emit_event_runs_async_handler(self):
        calls = []

        async def handler(event):
            calls.append(event["payload"]["message"])
            return {"ok": True}

        subscribe_event(EVENT_MESSAGE_RECEIVED, handler)

        with patch.object(event_bus, "log_event"):
            result = await emit_event(EVENT_MESSAGE_RECEIVED, {"message": "hello"}, {"source": "test"})

        self.assertTrue(result["success"])
        self.assertEqual(calls, ["hello"])
        self.assertTrue(result["handler_results"][0]["success"])
        self.assertEqual(result["event"]["metadata"]["source"], "test")

    async def test_handle_event_supports_sync_handler(self):
        def handler(event):
            return {"handled": event["name"]}

        subscribe_event(EVENT_LEAD_SAVED, handler)

        with patch.object(event_bus, "log_event"):
            results = await handle_event({"name": EVENT_LEAD_SAVED, "event_id": "evt-1", "payload": {}, "metadata": {}})

        self.assertTrue(results[0]["success"])
        self.assertEqual(results[0]["result"], {"handled": EVENT_LEAD_SAVED})

    async def test_handler_failure_returns_structured_result(self):
        async def bad_handler(event):
            raise RuntimeError("boom")

        subscribe_event(EVENT_APPOINTMENT_BOOKED, bad_handler)

        with (
            patch.object(event_bus, "log_error"),
            patch.object(event_bus, "log_event"),
            patch.object(retry_handler.logger, "exception"),
        ):
            results = await handle_event(
                {"name": EVENT_APPOINTMENT_BOOKED, "event_id": "evt-1", "payload": {}, "metadata": {}},
                retry_config=RetryConfig(max_attempts=1, base_delay_seconds=0, jitter_seconds=0, timeout_seconds=1),
            )

        self.assertFalse(results[0]["success"])
        self.assertEqual(results[0]["error_type"], "RetryExhaustedError")

    async def test_emit_event_can_publish_to_redis(self):
        redis_client = AsyncMock()

        with (
            patch.object(event_bus, "_get_redis_client", return_value=redis_client),
            patch.object(event_bus, "log_event"),
        ):
            result = await emit_event(EVENT_MESSAGE_RECEIVED, {"message": "hello"}, publish_redis=True, handle_local=False)

        self.assertTrue(result["redis_published"])
        redis_client.publish.assert_awaited_once()

    async def test_emit_event_validates_name(self):
        with self.assertRaises(ValueError):
            await emit_event("", {})

    async def test_close_event_bus_closes_redis(self):
        client = AsyncMock()
        event_bus._redis_client = client

        await close_event_bus()

        client.aclose.assert_awaited_once()
        self.assertIsNone(event_bus._redis_client)


if __name__ == "__main__":
    unittest.main()
