import httpx
from twilio.twiml.messaging_response import MessagingResponse

from app.config.settings import settings
from app.core.logger import log_error, log_event


class TwilioServiceError(RuntimeError):
    """Raised when an outbound Twilio message cannot be sent."""


def build_twiml_response(message: str) -> str:
    """
    Build a Twilio MessagingResponse.

    Twilio expects valid TwiML XML from webhooks. Returning this XML sends the
    chatbot reply back to the same SMS or WhatsApp conversation.
    """
    response = MessagingResponse()
    response.message(message)
    return str(response)


def _format_whatsapp_number(phone_number: str, *, field_name: str) -> str:
    raw_number = str(phone_number or "").strip()
    if not raw_number:
        raise TwilioServiceError(f"{field_name} phone number is required")

    if raw_number.startswith("whatsapp:"):
        formatted_number = raw_number
    elif raw_number.startswith("+"):
        formatted_number = f"whatsapp:{raw_number}"
    else:
        raise TwilioServiceError(f"{field_name} must be a WhatsApp number like whatsapp:+1234567890")

    number_part = formatted_number.removeprefix("whatsapp:")
    if not number_part.startswith("+") or not number_part[1:].isdigit() or not 8 <= len(number_part[1:]) <= 15:
        raise TwilioServiceError(f"{field_name} must be a valid E.164 WhatsApp number")

    return formatted_number


def _validate_message_body(message: str) -> str:
    body = str(message or "").strip()
    if not body:
        raise TwilioServiceError("message body is required")
    return body


async def send_whatsapp_message(phone_number: str, message: str) -> dict:
    """
    Send an autonomous outbound WhatsApp/SMS message through Twilio.

    Twilio's Python client is synchronous, so this backend uses httpx.AsyncClient to
    keep scheduler jobs from blocking the FastAPI event loop.
    """
    if settings.missing_twilio_values:
        raise TwilioServiceError(f"Missing Twilio settings: {', '.join(settings.missing_twilio_values)}")

    url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Messages.json"
    from_number = _format_whatsapp_number(settings.twilio_whatsapp_number, field_name="from")
    to_number = _format_whatsapp_number(phone_number, field_name="to")
    body = _validate_message_body(message)
    payload = {
        "From": from_number,
        "To": to_number,
        "Body": body,
    }

    log_event(
        "twilio_payload",
        from_number=from_number,
        to_number=to_number,
        body=body,
    )

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                url,
                data=payload,
                auth=(settings.twilio_account_sid, settings.twilio_auth_token),
            )
            log_event(
                "twilio_response",
                from_number=from_number,
                to_number=to_number,
                status_code=response.status_code,
            )
            response.raise_for_status()
            data = response.json()
            log_event(
                "twilio_message_sent",
                from_number=from_number,
                to_number=to_number,
                status_code=response.status_code,
                sid=data.get("sid"),
                twilio_status=data.get("status"),
            )
    except httpx.HTTPStatusError as exc:
        response_text = exc.response.text
        log_error(
            "Twilio API rejected WhatsApp message",
            from_number=from_number,
            to_number=to_number,
            status_code=exc.response.status_code,
            response_body=response_text,
        )
        raise TwilioServiceError("failed to send Twilio message") from exc
    except httpx.RequestError as exc:
        log_error(
            "Twilio API request failed",
            from_number=from_number,
            to_number=to_number,
            error_type=type(exc).__name__,
            error=str(exc),
        )
        raise TwilioServiceError("failed to send Twilio message") from exc
    except Exception as exc:
        log_error(
            "Unexpected Twilio delivery failure",
            from_number=from_number,
            to_number=to_number,
            error_type=type(exc).__name__,
            error=str(exc),
        )
        raise TwilioServiceError("failed to send Twilio message") from exc

    return {"sid": data.get("sid"), "status": data.get("status"), "to": to_number}
