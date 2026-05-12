import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.queue import worker
from app.queue.worker import (
    enqueue_task,
    get_task_status,
    process_task,
    recover_failed_jobs,
    start_worker,
)


class QueueTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.queue = MagicMock()
        self.queue.connection = MagicMock()
        self.queue_patch = patch.object(worker, "_get_queue", return_value=self.queue)
        self.queue_patch.start()

    def tearDown(self):
        self.queue_patch.stop()

    async def test_enqueue_task_returns_job_metadata(self):
        job = MagicMock()
        job.id = "job-123"
        job.get_status.return_value = "queued"
        self.queue.enqueue.return_value = job

        result = await enqueue_task(
            "send_email",
            args={"to": "a@test.com", "subject": "Hi", "body": "Hello"},
            user_id="user-123",
            job_id="job-123",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["job_id"], "job-123")
        self.assertEqual(result["data"]["task_name"], "send_email")
        self.queue.enqueue.assert_called_once()

    async def test_process_task_executes_tool_router(self):
        with patch.object(worker, "_execute_tool", new=AsyncMock(return_value={"success": True, "result": "ok"})):
            result = process_task("save_memory", {"user_id": "user-123", "message": "hello"})

        self.assertEqual(result["task_name"], "save_memory")
        self.assertEqual(result["user_id"], "user-123")
        self.assertEqual(result["result"]["success"], True)

    async def test_process_task_raises_on_tool_failure(self):
        with (
            patch.object(worker, "_execute_tool", new=AsyncMock(return_value={"success": False, "error": "bad"})),
            patch.object(worker.logger, "error"),
        ):
            with self.assertRaises(worker.QueueSystemError):
                process_task("missing_tool", {})

    async def test_get_task_status_returns_job_details(self):
        job = MagicMock()
        job.id = "job-123"
        job.result = {"ok": True}
        job.exc_info = None
        job.meta = {"user_id": "user-123"}
        job.created_at = None
        job.ended_at = None
        job.get_status.return_value = "finished"

        with patch.object(worker.Job, "fetch", return_value=job):
            result = await get_task_status("job-123")

        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["status"], "finished")
        self.assertEqual(result["data"]["metadata"]["user_id"], "user-123")

    async def test_recover_failed_jobs_requeues_failed_jobs(self):
        registry = MagicMock()
        registry.get_job_ids.return_value = ["job-1", "job-2"]

        with patch.object(worker, "FailedJobRegistry", return_value=registry):
            result = await recover_failed_jobs(limit=10)

        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["recovered_job_ids"], ["job-1", "job-2"])
        self.assertEqual(registry.requeue.call_count, 2)

    async def test_start_worker_runs_worker(self):
        worker_instance = MagicMock()
        worker_instance.work.return_value = True

        with (
            patch.object(worker, "_get_redis_connection", return_value=MagicMock()),
            patch.object(worker, "SimpleWorker", return_value=worker_instance),
        ):
            result = await start_worker(["agent_tasks"], burst=True, simple_worker=True)

        self.assertTrue(result["success"])
        self.assertTrue(result["data"]["worked"])
        worker_instance.work.assert_called_once_with(burst=True)


if __name__ == "__main__":
    unittest.main()
