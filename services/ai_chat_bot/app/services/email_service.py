import asyncio
import re
import smtplib
import socket
from email.message import EmailMessage
from smtplib import SMTPAuthenticationError, SMTPException
from typing import Any

from app.core.config import (
    EMAIL_FROM,
    EMAIL_HOST,
    EMAIL_PASS,
    EMAIL_PORT,
    EMAIL_RETRY_ATTEMPTS,
    EMAIL_TIMEOUT_SECONDS,
    EMAIL_USER,
)
from app.core.event_bus import EVENT_EMAIL_SENT, emit_event
from app.core.logger import log_error, log_event, log_info
from app.services.owner_settings_service import get_active_owner_emails

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class EmailServiceError(RuntimeError):
    """Raised when summary email delivery fails."""


def normalize_gmail_app_password(password: str | None = None) -> str:
    """Gmail app passwords are often copied as four groups; SMTP needs no spaces."""
    return "".join(str(password if password is not None else EMAIL_PASS or "").split())


def normalize_email_address(email: str) -> str:
    normalized = str(email or "").strip().lower()
    if not EMAIL_PATTERN.match(normalized):
        raise EmailServiceError(f"invalid email address: {normalized or '<empty>'}")
    return normalized


def validate_email_settings() -> dict[str, Any]:
    missing = []
    if not EMAIL_HOST:
        missing.append("EMAIL_HOST")
    if not EMAIL_PORT:
        missing.append("EMAIL_PORT")
    if not EMAIL_USER:
        missing.append("EMAIL_USER")
    if not normalize_gmail_app_password():
        missing.append("EMAIL_PASS")
    if not EMAIL_FROM:
        missing.append("EMAIL_FROM")

    status = {
        "valid": not missing,
        "missing": missing,
        "host": EMAIL_HOST,
        "port": EMAIL_PORT,
        "user_configured": bool(EMAIL_USER),
        "from_configured": bool(EMAIL_FROM),
        "password_configured": bool(normalize_gmail_app_password()),
    }
    if missing:
        log_error("SMTP email configuration incomplete", missing=missing)
    else:
        log_event("smtp_email_configuration_validated", host=EMAIL_HOST, port=EMAIL_PORT, email_user=EMAIL_USER)
    return status


def log_email_startup_validation() -> None:
    """Log startup warnings without blocking WhatsApp/chat service startup."""
    status = validate_email_settings()
    if not status["valid"]:
        log_error(
            "Summary emails are disabled until SMTP env vars are configured",
            missing=status["missing"],
            required="EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASS, EMAIL_FROM",
        )


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


def _validated_recipients(recipients: list[str]) -> list[str]:
    normalized = sorted({normalize_email_address(recipient) for recipient in recipients if str(recipient or "").strip()})
    if not normalized:
        raise EmailServiceError("at least one valid recipient is required")
    return normalized


def _smtp_error_message(exc: Exception) -> str:
    if isinstance(exc, SMTPAuthenticationError):
        return "Gmail SMTP authentication failed. Check EMAIL_USER, app password, and Gmail 2FA/app-password setup."
    if isinstance(exc, socket.timeout | TimeoutError):
        return "Gmail SMTP connection timed out."
    if isinstance(exc, ConnectionRefusedError):
        return "Gmail SMTP connection refused from this environment."
    if isinstance(exc, SMTPException):
        return f"Gmail SMTP error: {exc.__class__.__name__}"
    return f"Email delivery failed: {exc.__class__.__name__}"


def _send_email_once(recipients: list[str], subject: str, body: str, html_body: str | None = None) -> None:
    status = validate_email_settings()
    if not status["valid"]:
        raise EmailServiceError(f"missing SMTP settings: {', '.join(status['missing'])}")

    clean_recipients = _validated_recipients(recipients)
    from_email = normalize_email_address(EMAIL_FROM or EMAIL_USER or "")
    password = normalize_gmail_app_password()

    message = EmailMessage()
    message["From"] = from_email
    message["To"] = ", ".join(clean_recipients)
    message["Subject"] = str(subject or "AI Conversation Summary")
    message.set_content(body or "")
    if html_body:
        message.add_alternative(html_body, subtype="html")

    log_info("Connecting to Gmail SMTP...", host=EMAIL_HOST, port=EMAIL_PORT, recipients=clean_recipients)
    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=EMAIL_TIMEOUT_SECONDS) as smtp:
        smtp.ehlo()
        log_info("Starting SMTP TLS...", host=EMAIL_HOST, port=EMAIL_PORT)
        smtp.starttls()
        smtp.ehlo()
        log_info("Authenticating Gmail SMTP...", email_user=EMAIL_USER)
        smtp.login(EMAIL_USER, password)
        log_info("Sending summary email...", recipients=clean_recipients, subject=message["Subject"])
        smtp.send_message(message)


def _send_email_sync(recipients: list[str], subject: str, body: str, html_body: str | None = None) -> None:
    attempts = max(1, EMAIL_RETRY_ATTEMPTS)
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            log_event("smtp_email_attempt", attempt=attempt, attempts=attempts, recipient_count=len(recipients))
            _send_email_once(recipients, subject, body, html_body)
            log_event("smtp_email_sent", attempt=attempt, recipient_count=len(recipients))
            return
        except Exception as exc:
            last_error = exc
            log_error(
                "SMTP email attempt failed",
                attempt=attempt,
                attempts=attempts,
                error_type=type(exc).__name__,
                error=_smtp_error_message(exc),
            )
            if isinstance(exc, SMTPAuthenticationError):
                break
    raise EmailServiceError(_smtp_error_message(last_error or RuntimeError("unknown SMTP failure"))) from last_error


async def send_summary_email(user_id: str, phone_number: str, summary: dict[str, Any]) -> dict[str, Any]:
    recipients = await get_active_owner_emails()
    if not recipients:
        raise EmailServiceError("no active owner emails configured")

    subject = f"Closed sales chatbot conversation: {phone_number}"
    body = _build_summary_body(user_id, phone_number, summary)

    try:
        await asyncio.to_thread(_send_email_sync, recipients, subject, body)
    except Exception as exc:
        log_error("Summary email delivery failed", user_id=user_id, recipients=recipients, error_type=type(exc).__name__, error=str(exc))
        raise EmailServiceError("failed to send summary email") from exc

    log_event("email_sent", user_id=user_id, recipients=recipients)
    await emit_event(EVENT_EMAIL_SENT, {"user_id": user_id, "phone_number": phone_number, "recipients": recipients}, handle_local=True)
    return {"sent": True, "recipients": recipients}


async def send_html_email(recipients: list[str], subject: str, text_body: str, html_body: str) -> dict[str, Any]:
    """Send a Unicode-safe multipart text/HTML email report."""
    if not recipients:
        raise EmailServiceError("at least one recipient is required")

    try:
        log_info("Preparing HTML email...", recipients=recipients, subject=subject)
        await asyncio.to_thread(_send_email_sync, recipients, subject, text_body, html_body)
    except Exception as exc:
        log_error("HTML email delivery failed", recipients=recipients, error_type=type(exc).__name__, error=str(exc))
        raise EmailServiceError(str(exc)) from exc

    log_event("html_email_sent", recipients=recipients, subject=subject)
    await emit_event(EVENT_EMAIL_SENT, {"recipients": recipients, "subject": subject}, handle_local=True)
    return {"sent": True, "recipients": recipients, "subject": subject}


async def send_test_email(recipient: str | None = None) -> dict[str, Any]:
    """Verify Gmail SMTP settings and deliverability from FastAPI or Docker."""
    recipients = [recipient] if recipient else await get_active_owner_emails()
    if not recipients and EMAIL_FROM:
        recipients = [EMAIL_FROM]
    subject = "AI Chat Bot SMTP Test Email"
    text_body = "SMTP test succeeded. AI summary emails can be delivered from this backend."
    html_body = """
    <div style="font-family:Arial,sans-serif;background:#f4f7fb;padding:24px">
      <div style="max-width:640px;margin:auto;background:#fff;border:1px solid #dce5f2;padding:24px">
        <h2 style="color:#0f2747;margin-top:0">SMTP Test Successful</h2>
        <p>AI conversation summary emails can be delivered from this FastAPI backend.</p>
      </div>
    </div>
    """.strip()
    await send_html_email(recipients, subject, text_body, html_body)
    return {"success": True, "message": "Test email sent successfully", "recipients": _validated_recipients(recipients)}
