import asyncio
import logging
import threading
from datetime import UTC, datetime
from typing import Any

import redis
from redis.exceptions import RedisError
from rq import Queue, Retry, SimpleWorker, Worker
from rq.job import Job
from rq.registry import FailedJobRegistry

from app.core.config import REDIS_URL

logger = logging.getLogger(__name__)

DEFAULT_QUEUE_NAME = "agent_tasks"
DEFAULT_JOB_TIMEOUT_SECONDS = 300
DEFAULT_RESULT_TTL_SECONDS = 24 * 60 * 60
DEFAULT_FAILURE_TTL_SECONDS = 7 * 24 * 60 * 60
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_INTERVAL_SECONDS = [10, 30, 60]

_redis_connection: redis.Redis | None = None
_queues: dict[str, Queue] = {}


class QueueSystemError(RuntimeError):
    """Raised when queue operations fail."""


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _structured_response(
    *,
    success: bool,
    action: str,
    data: Any = None,
    error: str | None = None,
    error_type: str | None = None,
) -> dict[str, Any]:
    return {
        "success": success,
        "action": action,
        "data": data,
        "error": error,
        "error_type": error_type,
        "timestamp": _utc_now(),
    }


def _get_redis_connection() -> redis.Redis:
    """Reuse one sync Redis connection pool for RQ workers and producers."""
    global _redis_connection

    if not REDIS_URL:
        raise QueueSystemError("REDIS_URL is not configured")

    if _redis_connection is None:
        _redis_connection = redis.from_url(
            REDIS_URL,
            decode_responses=False,
            socket_connect_timeout=5,
            socket_timeout=10,
            retry_on_timeout=True,
        )

    return _redis_connection


def _get_queue(queue_name: str = DEFAULT_QUEUE_NAME) -> Queue:
    """Create or reuse an RQ Queue for a named workload."""
    if queue_name not in _queues:
        _queues[queue_name] = Queue(queue_name, connection=_get_redis_connection())

    return _queues[queue_name]


def _run_async(coro):
    """
    Run async tool-router work from RQ's synchronous worker process.

    RQ calls job functions synchronously. This adapter keeps the public processing
    path compatible with async tools without requiring a separate queue library.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    result: dict[str, Any] = {}

    def _runner() -> None:
        try:
            result["value"] = asyncio.run(coro)
        except Exception as exc:
            result["error"] = exc

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
    thread.join()

    if "error" in result:
        raise result["error"]

    return result.get("value")


def process_task(task_name: str, args: dict[str, Any] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    RQ job entrypoint for autonomous agent tasks.

    `task_name` should match a registered Tool Router tool, such as send_email,
    create_lead, book_meeting, or a future WhatsApp tool.
    """
    args = args or {}
    metadata = metadata or {}
    user_id = metadata.get("user_id") or args.get("user_id")

    logger.info("Processing queued task: task=%s user_id=%s", task_name, user_id)

    try:
        result = _run_async(_execute_tool(task_name, args))
    except Exception as exc:
        logger.exception("Queued task crashed: task=%s user_id=%s", task_name, user_id)
        raise QueueSystemError("queued task failed") from exc

    if not result.get("success"):
        logger.error("Queued task returned failure: task=%s user_id=%s result=%s", task_name, user_id, result)
        raise QueueSystemError(result.get("error") or "queued task returned failure")

    logger.info("Queued task completed: task=%s user_id=%s", task_name, user_id)
    return {
        "task_name": task_name,
        "user_id": user_id,
        "metadata": metadata,
        "result": result,
        "processed_at": _utc_now(),
    }


async def _execute_tool(task_name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Lazy wrapper keeps the queue module import-light for worker startup."""
    from app.core.tool_router import execute_tool

    return await execute_tool(task_name, args)


async def enqueue_task(
    task_name: str,
    args: dict[str, Any] | None = None,
    user_id: str | None = None,
    queue_name: str = DEFAULT_QUEUE_NAME,
    job_id: str | None = None,
    timeout: int = DEFAULT_JOB_TIMEOUT_SECONDS,
    retry_attempts: int = DEFAULT_RETRY_ATTEMPTS,
    retry_intervals: list[int] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Enqueue a tool-router task for background processing."""
    if not task_name or not task_name.strip():
        raise ValueError("task_name is required")

    args = args or {}
    metadata = {
        "user_id": user_id or args.get("user_id"),
        "task_type": task_name,
        "queued_at": _utc_now(),
        **(metadata or {}),
    }

    def _enqueue() -> Job:
        queue = _get_queue(queue_name)
        return queue.enqueue(
            process_task,
            task_name,
            args,
            metadata,
            job_id=job_id,
            job_timeout=timeout,
            result_ttl=DEFAULT_RESULT_TTL_SECONDS,
            failure_ttl=DEFAULT_FAILURE_TTL_SECONDS,
            retry=Retry(max=max(0, retry_attempts), interval=retry_intervals or DEFAULT_RETRY_INTERVAL_SECONDS),
            meta=metadata,
        )

    try:
        job = await asyncio.to_thread(_enqueue)
    except (RedisError, Exception) as exc:
        logger.exception("Failed to enqueue task: task=%s user_id=%s", task_name, metadata.get("user_id"))
        raise QueueSystemError("failed to enqueue task") from exc

    logger.info("Queued task: job_id=%s task=%s user_id=%s", job.id, task_name, metadata.get("user_id"))
    return _structured_response(
        success=True,
        action="enqueue_task",
        data={
            "job_id": job.id,
            "queue": queue_name,
            "task_name": task_name,
            "status": job.get_status(refresh=False),
            "metadata": metadata,
            "timeout": timeout,
            "retry_attempts": retry_attempts,
        },
    )


async def get_task_status(job_id: str, queue_name: str = DEFAULT_QUEUE_NAME) -> dict[str, Any]:
    """Return RQ task status, result, and failure details for tracking."""
    if not job_id or not job_id.strip():
        raise ValueError("job_id is required")

    def _fetch() -> dict[str, Any]:
        queue = _get_queue(queue_name)
        job = Job.fetch(job_id, connection=queue.connection)
        return {
            "job_id": job.id,
            "queue": queue_name,
            "status": job.get_status(refresh=True),
            "result": job.result,
            "exc_info": job.exc_info,
            "metadata": job.meta,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "ended_at": job.ended_at.isoformat() if job.ended_at else None,
        }

    try:
        data = await asyncio.to_thread(_fetch)
    except Exception as exc:
        logger.exception("Failed to fetch task status: job_id=%s", job_id)
        return _structured_response(
            success=False,
            action="get_task_status",
            error=str(exc),
            error_type=type(exc).__name__,
        )

    return _structured_response(success=True, action="get_task_status", data=data)


async def recover_failed_jobs(queue_name: str = DEFAULT_QUEUE_NAME, limit: int = 50) -> dict[str, Any]:
    """Requeue failed jobs for recovery after transient provider or network errors."""
    def _recover() -> list[str]:
        queue = _get_queue(queue_name)
        registry = FailedJobRegistry(queue=queue)
        recovered_job_ids = []
        for job_id in registry.get_job_ids()[: max(1, limit)]:
            registry.requeue(job_id)
            recovered_job_ids.append(job_id)
        return recovered_job_ids

    try:
        recovered = await asyncio.to_thread(_recover)
    except Exception as exc:
        logger.exception("Failed to recover jobs from queue=%s", queue_name)
        raise QueueSystemError("failed to recover failed jobs") from exc

    return _structured_response(
        success=True,
        action="recover_failed_jobs",
        data={"queue": queue_name, "recovered_job_ids": recovered, "count": len(recovered)},
    )


async def start_worker(
    queue_names: list[str] | None = None,
    burst: bool = False,
    simple_worker: bool = False,
) -> dict[str, Any]:
    """
    Start an RQ worker for one or more queues.

    In production this is normally launched in a separate process/container, not
    inside the FastAPI web process.
    """
    names = queue_names or [DEFAULT_QUEUE_NAME]

    def _work() -> bool:
        queues = [_get_queue(name) for name in names]
        worker_class = SimpleWorker if simple_worker else Worker
        worker = worker_class(queues, connection=_get_redis_connection())
        return worker.work(burst=burst)

    try:
        worked = await asyncio.to_thread(_work)
    except Exception as exc:
        logger.exception("RQ worker failed for queues=%s", names)
        raise QueueSystemError("worker failed") from exc

    return _structured_response(
        success=True,
        action="start_worker",
        data={"queues": names, "burst": burst, "worked": worked},
    )
