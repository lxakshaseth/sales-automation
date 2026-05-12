from datetime import datetime, timedelta, timezone

from apscheduler.triggers.date import DateTrigger

from app.core.config import CLOSE_AFTER_MINUTES
from app.core.logger import log_error, log_event
from app.scheduler.followup import cancel_followup, scheduler
from app.services.conversation_service import (
    STATUS_OPEN,
    close_conversation,
    get_conversation_history,
    get_conversation_state,
    inactive_minutes,
)
from app.services.email_service import EmailServiceError, send_summary_email
from app.services.groq_service import GroqServiceError
from app.services.language_service import get_localized_message
from app.services.summary_service import SummaryServiceError, generate_conversation_summary
from app.services.whatsapp_cloud_service import WhatsAppCloudError, send_text_message

AUTO_CLOSE_MESSAGE = "I will close this conversation for now. Feel free to message anytime if you need assistance."


def close_job_id(user_id: str) -> str:
    return f"conversation-close:{user_id}"


async def _run_close_job(user_id: str) -> dict:
    """
    Close a conversation only if it is still inactive at the 5-minute mark.

    The job generates an AI lead summary, emails owners, sends a polite closing
    message, and then marks the Redis lifecycle state as closed.
    """
    state = await get_conversation_state(user_id)
    if not state:
        return {"closed": False, "reason": "state_not_found"}
    if state.get("conversation_status") != STATUS_OPEN:
        return {"closed": False, "reason": "conversation_not_open"}
    if inactive_minutes(state) < CLOSE_AFTER_MINUTES:
        return {"closed": False, "reason": "user_replied_recently"}

    log_event(
        "close_chat_triggered",
        user_id=user_id,
        phone_number=state.get("phone_number"),
        preferred_language=state.get("preferred_language"),
    )
    history = await get_conversation_history(user_id)
    try:
        summary = await generate_conversation_summary(user_id, history)
    except (SummaryServiceError, GroqServiceError) as exc:
        log_error("Close-chat AI summary failed", user_id=user_id, error_type=type(exc).__name__)
        summary = {
            "customer_intent": "Unknown",
            "summary": "AI summary generation failed. Please review the chat history manually.",
            "lead_quality": "Needs review",
            "recommended_action": "Open the conversation history and follow up manually.",
        }

    email_result = {"sent": False}
    try:
        email_result = await send_summary_email(user_id, state["phone_number"], summary)
        log_event("summary_email_sent", user_id=user_id, recipients=email_result.get("recipients", []))
    except EmailServiceError as exc:
        log_error("Close-chat summary email failed", user_id=user_id, error=str(exc))

    try:
        auto_close_message = get_localized_message("auto_close", state.get("preferred_language"))
        await send_text_message(state["phone_number"], auto_close_message)
    except WhatsAppCloudError as exc:
        log_error("Auto-close message delivery failed", user_id=user_id, error=str(exc))

    closed_state = await close_conversation(user_id, summary)
    log_event("close_chat_job_completed", user_id=user_id, email_sent=email_result.get("sent", False))
    return {"closed": True, "state": closed_state, "summary": summary, "email": email_result}


async def _protected_close_job(user_id: str) -> dict:
    try:
        return await _run_close_job(user_id)
    except Exception as exc:
        log_error("Close-chat scheduler job failed", user_id=user_id, error_type=type(exc).__name__)
        raise


async def schedule_auto_close(user_id: str) -> dict:
    """Schedule the state-aware auto-close job for one active conversation."""
    run_at = datetime.now(timezone.utc) + timedelta(minutes=CLOSE_AFTER_MINUTES)
    job_id = close_job_id(user_id)
    existing_job = scheduler.get_job(job_id)
    if existing_job:
        scheduler.remove_job(job_id)
        log_event("close_chat_job_replaced", user_id=user_id, job_id=job_id)

    scheduler.add_job(
        _protected_close_job,
        trigger=DateTrigger(run_date=run_at, timezone=timezone.utc),
        id=job_id,
        kwargs={"user_id": user_id},
        replace_existing=True,
        name=f"auto close conversation for {user_id}",
    )
    log_event("close_chat_job_scheduled", user_id=user_id, job_id=job_id, run_at=run_at.isoformat())
    return {"job_id": job_id, "user_id": user_id, "task_type": "auto_close", "scheduled_time": run_at.isoformat()}


async def cancel_auto_close(user_id: str) -> dict:
    return await cancel_followup(close_job_id(user_id))
