import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

from app.services import conversation_service
from app.services.conversation_service import inactive_minutes, record_message_received
from app.services.reminder_service import send_inactivity_reminder


class ConversationLifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def test_record_message_received_updates_state_memory_and_schedulers(self):
        with (
            patch.object(conversation_service, "get_conversation_state", new=AsyncMock(return_value=None)),
            patch.object(conversation_service, "save_conversation_state", new=AsyncMock()) as save_state,
            patch.object(conversation_service, "append_memory", new=AsyncMock()) as append_memory,
            patch("app.scheduler.reminder_scheduler.schedule_inactivity_reminder", new=AsyncMock()) as schedule_reminder,
            patch("app.scheduler.close_chat_scheduler.schedule_auto_close", new=AsyncMock()) as schedule_close,
            patch.object(conversation_service, "emit_event", new=AsyncMock()),
        ):
            state = await record_message_received("user-1", "whatsapp:+1000", "Hello")

        self.assertEqual(state["conversation_status"], "open")
        self.assertFalse(state["reminder_sent"])
        self.assertEqual(state["preferred_language"], "en")
        self.assertEqual(state["last_language_detected"], "en")
        save_state.assert_awaited_once()
        append_memory.assert_awaited_once()
        schedule_reminder.assert_awaited_once_with("user-1")
        schedule_close.assert_awaited_once_with("user-1")

    def test_inactive_minutes_uses_last_message_time(self):
        last_message_time = datetime.now(UTC) - timedelta(minutes=3)
        state = {"last_message_time": last_message_time.isoformat()}

        self.assertGreaterEqual(inactive_minutes(state), 2.9)

    async def test_reminder_skips_when_user_recently_replied(self):
        state = {
            "user_id": "user-1",
            "phone_number": "whatsapp:+1000",
            "conversation_status": "open",
            "reminder_sent": False,
            "last_message_time": datetime.now(UTC).isoformat(),
        }

        with patch("app.services.reminder_service.get_conversation_state", new=AsyncMock(return_value=state)):
            result = await send_inactivity_reminder("user-1")

        self.assertFalse(result["sent"])
        self.assertEqual(result["reason"], "user_replied_recently")

    async def test_record_message_received_persists_language_switch(self):
        existing = {
            "user_id": "user-1",
            "phone_number": "whatsapp:+1000",
            "preferred_language": "en",
            "language_confidence": 0.99,
            "conversation_start_time": datetime.now(UTC).isoformat(),
        }

        with (
            patch.object(conversation_service, "get_conversation_state", new=AsyncMock(return_value=existing)),
            patch.object(conversation_service, "save_conversation_state", new=AsyncMock()) as save_state,
            patch.object(conversation_service, "append_memory", new=AsyncMock()),
            patch("app.scheduler.reminder_scheduler.schedule_inactivity_reminder", new=AsyncMock()),
            patch("app.scheduler.close_chat_scheduler.schedule_auto_close", new=AsyncMock()),
            patch.object(conversation_service, "emit_event", new=AsyncMock()),
        ):
            state = await record_message_received("user-1", "whatsapp:+1000", "Can you continue in Hindi?")

        self.assertEqual(state["preferred_language"], "hi")
        self.assertTrue(state["language_switch_requested"])
        self.assertIn("हिंदी", state["language_switch_confirmation"])
        save_state.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
