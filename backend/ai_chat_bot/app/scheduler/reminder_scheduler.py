from datetime import datetime, timedelta, timezone

from apscheduler.triggers.date import DateTrigger

from app.core.config import REMINDER_AFTER_MINUTES
from app.core.logger import log_error, log_event
from app.scheduler.followup import cancel_followup, scheduler
from app.services.reminder_service import DEFAULT_REMINDER_MESSAGE, send_inactivity_reminder


def reminder_job_id(user_id: str) -> str:
    return f"conversation-reminder:{user_id}"


async def _run_reminder_job(user_id: str) -> dict:
    """APScheduler target that performs the state-aware inactivity reminder check."""
    try:
        result = await send_inactivity_reminder(user_id)
        log_event("reminder_job_completed", user_id=user_id, result=result)
        return result
    except Exception as exc:
        log_error("Reminder scheduler job failed", user_id=user_id, error_type=type(exc).__name__)
        raise


async def schedule_inactivity_reminder(user_id: str) -> dict:
    """
    Schedule the 2-minute inactivity reminder for one user.

    replace_existing=True inside the shared scheduler means every incoming message
    refreshes the timer, which is what lets multiple users run independently.
    """
    run_at = datetime.now(timezone.utc) + timedelta(minutes=REMINDER_AFTER_MINUTES)
    job_id = reminder_job_id(user_id)
    existing_job = scheduler.get_job(job_id)
    if existing_job:
        scheduler.remove_job(job_id)
        log_event("reminder_job_replaced", user_id=user_id, job_id=job_id)

    scheduler.add_job(
        _run_reminder_job,
        trigger=DateTrigger(run_date=run_at, timezone=timezone.utc),
        id=job_id,
        kwargs={"user_id": user_id},
        replace_existing=True,
        name=f"inactivity reminder for {user_id}",
    )
    log_event("reminder_scheduled", user_id=user_id, job_id=job_id, run_at=run_at.isoformat())
    log_event("reminder_job_scheduled", user_id=user_id, job_id=job_id, run_at=run_at.isoformat())
    return {
        "job_id": job_id,
        "user_id": user_id,
        "task_type": "inactivity_reminder",
        "message": DEFAULT_REMINDER_MESSAGE,
        "scheduled_time": run_at.isoformat(),
    }


async def cancel_inactivity_reminder(user_id: str) -> dict:
    return await cancel_followup(reminder_job_id(user_id))
