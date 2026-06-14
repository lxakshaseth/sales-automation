import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

from app.scheduler import followup
from app.scheduler.close_chat_scheduler import close_job_id, schedule_auto_close
from app.scheduler.followup import (
    cancel_followup,
    list_jobs,
    schedule_24h_no_reply_followup,
    schedule_followup,
    schedule_reminder,
)
from app.scheduler.reminder_scheduler import reminder_job_id, schedule_inactivity_reminder


class SchedulerTests(unittest.IsolatedAsyncioTestCase):
    def tearDown(self):
        for job in followup.scheduler.get_jobs():
            followup.scheduler.remove_job(job.id)

    async def test_schedule_followup_adds_metadata(self):
        run_at = datetime.now(UTC) + timedelta(hours=1)

        result = await schedule_followup(
            user_id="user-123",
            message="Do you still need help?",
            scheduled_time=run_at,
            job_id="followup-test",
        )

        self.assertEqual(result["job_id"], "followup-test")
        self.assertEqual(result["user_id"], "user-123")
        self.assertEqual(result["task_type"], "followup")
        self.assertEqual(result["message"], "Do you still need help?")
        self.assertIsNotNone(followup.scheduler.get_job("followup-test"))

    async def test_schedule_reminder_uses_reminder_task_type(self):
        result = await schedule_reminder(
            user_id="user-123",
            message="Call the lead.",
            delay_seconds=3600,
            job_id="reminder-test",
        )

        self.assertEqual(result["task_type"], "reminder")

    async def test_list_jobs_returns_agent_metadata(self):
        await schedule_followup(
            user_id="user-123",
            message="Follow up soon.",
            delay_seconds=3600,
            job_id="list-test",
        )

        jobs = await list_jobs()

        self.assertEqual(jobs[0]["job_id"], "list-test")
        self.assertEqual(jobs[0]["user_id"], "user-123")
        self.assertEqual(jobs[0]["task_type"], "followup")

    async def test_cancel_followup_removes_job(self):
        await schedule_followup(
            user_id="user-123",
            message="Cancel me.",
            delay_seconds=3600,
            job_id="cancel-test",
        )

        result = await cancel_followup("cancel-test")

        self.assertTrue(result["success"])
        self.assertIsNone(followup.scheduler.get_job("cancel-test"))

    async def test_cancel_followup_handles_missing_job(self):
        result = await cancel_followup("missing-job")

        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "job not found")

    async def test_24h_no_reply_workflow(self):
        result = await schedule_24h_no_reply_followup(
            user_id="user-123",
            message="Checking in after no reply.",
            job_id="no-reply-test",
        )

        self.assertEqual(result["task_type"], "followup")
        self.assertEqual(result["job_id"], "no-reply-test")

    async def test_run_with_retries_dispatches_tool(self):
        metadata = {
            "job_id": "retry-test",
            "user_id": "user-123",
            "task_type": "followup",
            "scheduled_time": datetime.now(UTC).isoformat(),
            "message": "Send message",
            "retry_attempts": 2,
            "tool_name": "send_whatsapp",
            "tool_args": {"to": "+10000000000", "body": "Hello"},
        }

        with patch.object(followup, "_execute_tool", new=AsyncMock(return_value={"success": True})) as mock_tool:
            result = await followup._run_with_retries(metadata)

        self.assertTrue(result["success"])
        mock_tool.assert_awaited_once_with("send_whatsapp", metadata["tool_args"])

    async def test_conversation_reminder_replaces_existing_user_job(self):
        await schedule_inactivity_reminder("whatsapp:+15550000000")
        await schedule_inactivity_reminder("whatsapp:+15550000000")

        job_id = reminder_job_id("whatsapp:+15550000000")
        jobs = [job for job in followup.scheduler.get_jobs() if job.id == job_id]

        self.assertEqual(len(jobs), 1)

    async def test_auto_close_replaces_existing_user_job(self):
        await schedule_auto_close("whatsapp:+15550000000")
        await schedule_auto_close("whatsapp:+15550000000")

        job_id = close_job_id("whatsapp:+15550000000")
        jobs = [job for job in followup.scheduler.get_jobs() if job.id == job_id]

        self.assertEqual(len(jobs), 1)


if __name__ == "__main__":
    unittest.main()
