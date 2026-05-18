import asyncio

from app.core.config import REMINDER_AFTER_MINUTES
from app.core.event_bus import EVENT_REMINDER_SENT, emit_event
from app.core.logger import log_error, log_event
from app.services.conversation_service import STATUS_OPEN, get_conversation_state, inactive_minutes, mark_reminder_sent
from app.services.language_service import get_localized_message
from app.services.whatsapp_provider import WhatsAppProviderError, send_whatsapp_message

DEFAULT_REMINDER_MESSAGE = "Just checking in. Let me know if you'd like more details or a quick demo."


class ReminderServiceError(RuntimeError):
    """Raised when inactivity reminder handling fails."""


async def _send_reminder_with_retry(phone_number: str, message: str, *, user_id: str) -> dict:
    last_error: WhatsAppProviderError | None = None
    for attempt in range(1, 3):
        try:
            log_event("reminder_delivery_attempt", user_id=user_id, phone_number=phone_number, attempt=attempt)
            return await send_whatsapp_message(phone_number, message)
        except WhatsAppProviderError as exc:
            last_error = exc
            log_error("reminder_failed", user_id=user_id, phone_number=phone_number, attempt=attempt, error=str(exc))
            if attempt == 1:
                await asyncio.sleep(1)

    raise ReminderServiceError("failed to send inactivity reminder") from last_error


async def send_inactivity_reminder(user_id: str) -> dict:
    """
    Send a reminder only if the user is still inactive.

    The scheduler job calls this at the configured inactivity mark. The state check
    prevents old jobs from sending reminders after a user has already replied.
    """
    state = await get_conversation_state(user_id)
    if not state:
        return {"sent": False, "reason": "state_not_found"}

    if state.get("conversation_status") != STATUS_OPEN:
        return {"sent": False, "reason": "conversation_not_open"}

    if state.get("reminder_sent"):
        return {"sent": False, "reason": "already_sent"}

    if inactive_minutes(state) < REMINDER_AFTER_MINUTES:
        return {"sent": False, "reason": "user_replied_recently"}

    reminder_message = get_localized_message("reminder", state.get("preferred_language"))
    try:
        whatsapp_result = await _send_reminder_with_retry(
            state["phone_number"],
            reminder_message,
            user_id=user_id,
        )
    except ReminderServiceError as exc:
        log_error("reminder_delivery_exhausted", user_id=user_id, phone_number=state.get("phone_number"), error=str(exc))
        return {"sent": False, "reason": "delivery_failed", "error": str(exc)}

    await mark_reminder_sent(user_id)
    log_event(
        "reminder_delivered",
        user_id=user_id,
        phone_number=state.get("phone_number"),
        preferred_language=state.get("preferred_language"),
    )
    log_event("reminder_sent", user_id=user_id, phone_number=state.get("phone_number"))
    await emit_event(
        EVENT_REMINDER_SENT,
        {
            "user_id": user_id,
            "phone_number": state.get("phone_number"),
            "message": reminder_message,
            "preferred_language": state.get("preferred_language"),
        },
        handle_local=True,
    )
    return {"sent": True, "whatsapp": whatsapp_result}
