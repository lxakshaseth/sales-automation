import asyncio
import smtplib
from email.message import EmailMessage
from typing import Any

from app.core.config import SMTP_EMAIL, SMTP_HOST, SMTP_PASSWORD, SMTP_PORT
from app.core.event_bus import EVENT_EMAIL_SENT, emit_event
from app.core.logger import log_error, log_event
from app.services.owner_settings_service import get_active_owner_emails


class EmailServiceError(RuntimeError):
    """Raised when summary email delivery fails."""


def _build_summary_body(user_id: str, phone_number: str, summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "A sales chatbot conversation was automatically closed.",
            "",
            f"User ID: {user_id}",
            f"Phone: {phone_number}",
            "",
            f"Customer intent: {summary.get('customer_intent', '')}",
            f"Lead quality: {summary.get('lead_quality', '')}",
            f"Recommended action: {summary.get('recommended_action', '')}",
            "",
            "Summary:",
            str(summary.get("summary", "")),
        ]
    )


def _send_email_sync(recipients: list[str], subject: str, body: str) -> None:
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        raise EmailServiceError("SMTP_EMAIL and SMTP_PASSWORD are required")

    message = EmailMessage()
    message["From"] = SMTP_EMAIL
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as smtp:
        smtp.starttls()
        smtp.login(SMTP_EMAIL, SMTP_PASSWORD)
        smtp.send_message(message)


async def send_summary_email(user_id: str, phone_number: str, summary: dict[str, Any]) -> dict[str, Any]:
    """
    Email the owner team when a conversation closes.

    SMTP is blocking by nature, so it runs in a thread while the scheduler remains
    async-friendly. Multiple owner emails are loaded from .env and owner_settings.
    """
    recipients = await get_active_owner_emails()
    if not recipients:
        raise EmailServiceError("no active owner emails configured")

    subject = f"Closed sales chatbot conversation: {phone_number}"
    body = _build_summary_body(user_id, phone_number, summary)

    try:
        await asyncio.to_thread(_send_email_sync, recipients, subject, body)
    except Exception as exc:
        log_error("Summary email delivery failed", user_id=user_id, recipients=recipients, error_type=type(exc).__name__)
        raise EmailServiceError("failed to send summary email") from exc

    log_event("email_sent", user_id=user_id, recipients=recipients)
    await emit_event(
        EVENT_EMAIL_SENT,
        {"user_id": user_id, "phone_number": phone_number, "recipients": recipients},
        handle_local=True,
    )
    return {"sent": True, "recipients": recipients}
