import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, JobExecutionEvent
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from app.core.logger import log_error, log_event

logger = logging.getLogger(__name__)

DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_BACKOFF_SECONDS = 2.0

scheduler = AsyncIOScheduler(
    timezone=timezone.utc,
    job_defaults={
        "coalesce": True,
        "max_instances": 3,
        "misfire_grace_time": 300,
    },
)


class SchedulerError(RuntimeError):
    """Raised when follow-up scheduling fails."""


def _job_listener(event: JobExecutionEvent) -> None:
    if event.exception:
        logger.error("Scheduled job failed: job_id=%s", event.job_id, exc_info=event.exception)
        return

    logger.info("Scheduled job completed: job_id=%s", event.job_id)


if not scheduler._listeners:
    scheduler.add_listener(_job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_scheduled_time(
    scheduled_time: datetime | str | None,
    delay_seconds: int | float | None,
) -> datetime:
    """Accept either an absolute time or a relative delay for flexible agent workflows."""
    if scheduled_time is None and delay_seconds is None:
        raise ValueError("scheduled_time or delay_seconds is required")

    if scheduled_time is not None:
        if isinstance(scheduled_time, str):
            scheduled_time = datetime.fromisoformat(scheduled_time.replace("Z", "+00:00"))

        if scheduled_time.tzinfo is None:
            scheduled_time = scheduled_time.replace(tzinfo=timezone.utc)

        return scheduled_time.astimezone(timezone.utc)

    return _utc_now() + timedelta(seconds=float(delay_seconds or 0))


def _make_job_id(user_id: str, task_type: str, job_id: str | None = None) -> str:
    if job_id:
        return job_id

    return f"{task_type}:{user_id}:{uuid4().hex}"


async def start_scheduler() -> None:
    """Start the shared scheduler once during FastAPI startup."""
    if not scheduler.running:
        scheduler.start()
        logger.info("APScheduler started")


async def shutdown_scheduler() -> None:
    """Stop the scheduler during FastAPI shutdown without interrupting running jobs."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")


async def _dispatch_scheduled_task(metadata: dict[str, Any]) -> dict[str, Any]:
    """
    Execute the scheduled task.

    Today this records the task shape and optionally calls a registered tool. Later,
    WhatsApp, CRM, escalation, and appointment tools can be registered in the central
    tool router and referenced here via `tool_name`.
    """
    tool_name = metadata.get("tool_name")
    log_event(
        "scheduler_triggered",
        job_id=metadata.get("job_id"),
        user_id=metadata.get("user_id"),
        task_type=metadata.get("task_type"),
        tool_name=tool_name,
    )
    if not tool_name:
        logger.info(
            "Scheduled task ready: user_id=%s task_type=%s message=%s",
            metadata["user_id"],
            metadata["task_type"],
            metadata["message"],
        )
        return {"queued": True, "metadata": metadata}

    from app.core.tool_router import execute_tool

    tool_args = metadata.get("tool_args") or {}
    return await _execute_tool(tool_name, tool_args)


async def _execute_tool(tool_name: str, tool_args: dict[str, Any]) -> dict[str, Any]:
    """Lazy wrapper avoids importing the router while scheduler module loads."""
    from app.core.tool_router import execute_tool

    return await execute_tool(tool_name, tool_args)


async def _run_with_retries(metadata: dict[str, Any]) -> dict[str, Any]:
    attempts = max(1, int(metadata.get("retry_attempts", DEFAULT_RETRY_ATTEMPTS)))
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            result = await _dispatch_scheduled_task(metadata)
            log_event(
                "scheduler_task_success",
                job_id=metadata["job_id"],
                user_id=metadata.get("user_id"),
                task_type=metadata.get("task_type"),
                attempt=attempt,
                attempts=attempts,
            )
            logger.info(
                "Scheduled task succeeded: job_id=%s attempt=%s/%s",
                metadata["job_id"],
                attempt,
                attempts,
            )
            return {"success": True, "attempts": attempt, "result": result}
        except Exception as exc:
            last_error = exc
            log_error(
                "scheduler_task_attempt_failed",
                job_id=metadata["job_id"],
                user_id=metadata.get("user_id"),
                task_type=metadata.get("task_type"),
                attempt=attempt,
                attempts=attempts,
                error_type=type(exc).__name__,
                error=str(exc),
            )
            logger.exception(
                "Scheduled task failed: job_id=%s attempt=%s/%s",
                metadata["job_id"],
                attempt,
                attempts,
            )
            if attempt < attempts:
                await asyncio.sleep(DEFAULT_RETRY_BACKOFF_SECONDS * attempt)

    log_error(
        "scheduler_task_failed",
        job_id=metadata["job_id"],
        user_id=metadata.get("user_id"),
        task_type=metadata.get("task_type"),
        attempts=attempts,
        error=str(last_error),
    )
    return {"success": False, "attempts": attempts, "error": str(last_error)}


def _schedule_job(
    *,
    user_id: str,
    task_type: str,
    message: str,
    scheduled_time: datetime | str | None = None,
    delay_seconds: int | float | None = None,
    job_id: str | None = None,
    retry_attempts: int = DEFAULT_RETRY_ATTEMPTS,
    tool_name: str | None = None,
    tool_args: dict[str, Any] | None = None,
    extra_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not user_id or not str(user_id).strip():
        raise ValueError("user_id is required")

    if not message or not str(message).strip():
        raise ValueError("message is required")

    run_at = _normalize_scheduled_time(scheduled_time, delay_seconds)
    resolved_job_id = _make_job_id(str(user_id).strip(), task_type, job_id)
    metadata = {
        "job_id": resolved_job_id,
        "user_id": str(user_id).strip(),
        "task_type": task_type,
        "scheduled_time": run_at.isoformat(),
        "message": str(message),
        "retry_attempts": max(1, int(retry_attempts)),
        "tool_name": tool_name,
        "tool_args": tool_args or {},
        **(extra_metadata or {}),
    }

    try:
        existing_job = scheduler.get_job(resolved_job_id)
        if existing_job:
            scheduler.remove_job(resolved_job_id)
            logger.info("Replaced existing scheduled job: job_id=%s", resolved_job_id)

        scheduler.add_job(
            _run_with_retries,
            trigger=DateTrigger(run_date=run_at, timezone=timezone.utc),
            id=resolved_job_id,
            kwargs={"metadata": metadata},
            replace_existing=True,
            name=f"{task_type} for {user_id}",
        )
    except Exception as exc:
        logger.exception("Failed to schedule job: job_id=%s", resolved_job_id)
        raise SchedulerError("failed to schedule job") from exc

    logger.info("Scheduled job: job_id=%s run_at=%s", resolved_job_id, run_at.isoformat())
    return metadata


async def schedule_followup(
    user_id: str,
    message: str,
    scheduled_time: datetime | str | None = None,
    delay_seconds: int | float | None = None,
    job_id: str | None = None,
    retry_attempts: int = DEFAULT_RETRY_ATTEMPTS,
    tool_name: str | None = None,
    tool_args: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Schedule an autonomous delayed follow-up for one user."""
    return _schedule_job(
        user_id=user_id,
        task_type="followup",
        message=message,
        scheduled_time=scheduled_time,
        delay_seconds=delay_seconds,
        job_id=job_id,
        retry_attempts=retry_attempts,
        tool_name=tool_name,
        tool_args=tool_args,
    )


async def schedule_reminder(
    user_id: str,
    message: str,
    scheduled_time: datetime | str | None = None,
    delay_seconds: int | float | None = None,
    job_id: str | None = None,
    retry_attempts: int = DEFAULT_RETRY_ATTEMPTS,
    tool_name: str | None = None,
    tool_args: dict[str, Any] | None = None,
    task_type: str = "reminder",
    extra_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Schedule a reminder for CRM, appointment, or agent follow-up workflows."""
    return _schedule_job(
        user_id=user_id,
        task_type=task_type,
        message=message,
        scheduled_time=scheduled_time,
        delay_seconds=delay_seconds,
        job_id=job_id,
        retry_attempts=retry_attempts,
        tool_name=tool_name,
        tool_args=tool_args,
        extra_metadata=extra_metadata,
    )


async def cancel_followup(job_id: str) -> dict[str, Any]:
    """Cancel a scheduled follow-up or reminder by job id."""
    if not job_id or not str(job_id).strip():
        raise ValueError("job_id is required")

    job = scheduler.get_job(job_id)
    if job is None:
        return {"success": False, "job_id": job_id, "error": "job not found"}

    try:
        scheduler.remove_job(job_id)
    except Exception as exc:
        logger.exception("Failed to cancel job: job_id=%s", job_id)
        raise SchedulerError("failed to cancel job") from exc

    logger.info("Cancelled job: job_id=%s", job_id)
    return {"success": True, "job_id": job_id}


async def list_jobs() -> list[dict[str, Any]]:
    """Return scheduled jobs with the metadata required by autonomous agents."""
    jobs = []
    for job in scheduler.get_jobs():
        metadata = job.kwargs.get("metadata", {})
        next_run_time = getattr(job, "next_run_time", None)
        jobs.append(
            {
                "job_id": job.id,
                "name": job.name,
                "next_run_time": next_run_time.isoformat() if next_run_time else metadata.get("scheduled_time"),
                "user_id": metadata.get("user_id"),
                "task_type": metadata.get("task_type"),
                "scheduled_time": metadata.get("scheduled_time"),
                "message": metadata.get("message"),
            }
        )

    return sorted(jobs, key=lambda item: item["scheduled_time"] or "")


async def schedule_24h_no_reply_followup(user_id: str, message: str, job_id: str | None = None) -> dict[str, Any]:
    """Example workflow: if a user does not reply for 24 hours, schedule a follow-up."""
    return await schedule_followup(
        user_id=user_id,
        message=message,
        delay_seconds=24 * 60 * 60,
        job_id=job_id,
        retry_attempts=DEFAULT_RETRY_ATTEMPTS,
        tool_name="send_whatsapp",
        tool_args={"to": user_id, "message": message},
    )
