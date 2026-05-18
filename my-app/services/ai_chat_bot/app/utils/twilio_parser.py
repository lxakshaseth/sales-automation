from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class IncomingTwilioMessage:
    """Normalized Twilio SMS/WhatsApp webhook payload."""

    body: str
    from_number: str
    message_sid: str
    channel: str


class InvalidTwilioPayloadError(ValueError):
    """Raised when Twilio sends an incomplete webhook payload."""


def detect_channel(from_number: str) -> str:
    """Twilio WhatsApp numbers arrive as `whatsapp:+123...`; SMS is a plain number."""
    return "whatsapp" if from_number.startswith("whatsapp:") else "sms"


def parse_twilio_form(form_data: dict[str, Any]) -> IncomingTwilioMessage:
    """Extract the minimum fields needed by the chatbot webhook."""
    body = str(form_data.get("Body", "")).strip()
    from_number = str(form_data.get("From", "")).strip()
    message_sid = str(form_data.get("MessageSid", "")).strip()

    missing = []
    if not body:
        missing.append("Body")
    if not from_number:
        missing.append("From")
    if not message_sid:
        missing.append("MessageSid")

    if missing:
        raise InvalidTwilioPayloadError(f"Missing required Twilio field(s): {', '.join(missing)}")

    return IncomingTwilioMessage(
        body=body,
        from_number=from_number,
        message_sid=message_sid,
        channel=detect_channel(from_number),
    )
