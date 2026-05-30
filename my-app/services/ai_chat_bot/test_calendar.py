import unittest
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from app.tools import calendar_tool
from app.tools.calendar_tool import (
    book_meeting,
    cancel_meeting,
    close_calendar_client,
    create_event,
    get_upcoming_events,
    reschedule_meeting,
)


class CalendarToolTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        calendar_tool._access_token = "token"
        self.client = AsyncMock()
        self.client_patch = patch.object(calendar_tool, "_get_calendar_client", return_value=self.client)
        self.client_patch.start()

    def tearDown(self):
        self.client_patch.stop()
        calendar_tool._access_token = "token"

    def _response(self, status_code: int, data: dict | None = None):
        request = httpx.Request("GET", "https://www.googleapis.com/calendar/v3/test")
        if data is None:
            return httpx.Response(status_code, request=request)
        return httpx.Response(status_code, json=data, request=request)

    def _event(self):
        return {
            "id": "event-123",
            "summary": "Discovery call",
            "start": {"dateTime": "2026-05-08T10:00:00+05:30"},
            "end": {"dateTime": "2026-05-08T10:30:00+05:30"},
            "attendees": [{"email": "lead@example.com"}],
            "hangoutLink": "https://meet.google.com/test",
            "htmlLink": "https://calendar.google.com/event",
        }

    async def test_create_event_posts_calendar_payload(self):
        self.client.request.return_value = self._response(200, self._event())

        result = await create_event(
            user_id="user-123",
            title="Discovery call",
            start_time="2026-05-08T10:00:00+05:30",
            end_time="2026-05-08T10:30:00+05:30",
            attendees=["lead@example.com"],
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["event_id"], "event-123")
        self.assertEqual(result["data"]["meeting_link"], "https://meet.google.com/test")
        self.assertEqual(self.client.request.await_args.args[0], "POST")
        self.assertIn("/calendars/primary/events", self.client.request.await_args.args[1])
        payload = self.client.request.await_args.kwargs["json"]
        self.assertEqual(payload["extendedProperties"]["private"]["user_id"], "user-123")
        self.assertIn("conferenceData", payload)

    async def test_book_meeting_sends_confirmation_and_schedules_reminder(self):
        self.client.request.return_value = self._response(200, self._event())

        with (
            patch.object(calendar_tool, "send_email", new=AsyncMock(return_value={"id": "email-123"})) as mock_email,
            patch.object(calendar_tool, "_schedule_calendar_reminder", new=AsyncMock(return_value={"job_id": "reminder-123"})) as mock_reminder,
        ):
            result = await book_meeting(
                user_id="user-123",
                title="Discovery call",
                start_time="2026-05-08T10:00:00+05:30",
                end_time="2026-05-08T10:30:00+05:30",
                attendees=["lead@example.com"],
            )

        self.assertTrue(result["success"])
        self.assertTrue(result["data"]["confirmation_sent"])
        mock_email.assert_awaited_once()
        mock_reminder.assert_awaited_once()

    async def test_cancel_meeting_deletes_event(self):
        self.client.request.return_value = self._response(204)

        result = await cancel_meeting(user_id="user-123", event_id="event-123")

        self.assertTrue(result["success"])
        self.assertTrue(result["data"]["cancelled"])
        self.assertEqual(self.client.request.await_args.args[0], "DELETE")

    async def test_reschedule_meeting_patches_event(self):
        self.client.request.return_value = self._response(200, self._event())

        with patch.object(calendar_tool, "_schedule_calendar_reminder", new=AsyncMock(return_value={"job_id": "reminder-123"})):
            result = await reschedule_meeting(
                user_id="user-123",
                event_id="event-123",
                start_time="2026-05-08T11:00:00+05:30",
                end_time="2026-05-08T11:30:00+05:30",
            )

        self.assertTrue(result["success"])
        self.assertEqual(self.client.request.await_args.args[0], "PATCH")
        payload = self.client.request.await_args.kwargs["json"]
        self.assertEqual(payload["start"]["dateTime"], "2026-05-08T11:00:00+05:30")

    async def test_get_upcoming_events_returns_summaries(self):
        self.client.request.return_value = self._response(200, {"items": [self._event()]})

        result = await get_upcoming_events(user_id="user-123", max_results=100)

        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["events"][0]["event_id"], "event-123")
        self.assertEqual(self.client.request.await_args.kwargs["params"]["maxResults"], 50)

    async def test_request_refreshes_token_on_401(self):
        self.client.request.side_effect = [
            self._response(401, {"error": "unauthorized"}),
            self._response(200, self._event()),
        ]

        with (
            patch.object(calendar_tool, "_refresh_access_token", new=AsyncMock(return_value="new-token")),
            patch.object(calendar_tool.logger, "warning"),
        ):
            result = await create_event(
                user_id="user-123",
                title="Discovery call",
                start_time=datetime.now(UTC),
                end_time=datetime.now(UTC),
            )

        self.assertTrue(result["success"])
        self.assertEqual(self.client.request.await_count, 2)

    async def test_request_returns_structured_error(self):
        self.client.request.return_value = self._response(400, {"error": "bad request"})

        with patch.object(calendar_tool.logger, "warning"), patch.object(calendar_tool.logger, "error"):
            result = await get_upcoming_events(user_id="user-123")

        self.assertFalse(result["success"])
        self.assertEqual(result["error_type"], "HTTPStatusError")

    async def test_close_calendar_client(self):
        calendar_client = MagicMock()
        oauth_client = MagicMock()
        calendar_client.aclose = AsyncMock()
        oauth_client.aclose = AsyncMock()
        calendar_tool._calendar_client = calendar_client
        calendar_tool._oauth_client = oauth_client

        await close_calendar_client()

        calendar_client.aclose.assert_awaited_once()
        oauth_client.aclose.assert_awaited_once()
        self.assertIsNone(calendar_tool._calendar_client)
        self.assertIsNone(calendar_tool._oauth_client)


if __name__ == "__main__":
    unittest.main()
