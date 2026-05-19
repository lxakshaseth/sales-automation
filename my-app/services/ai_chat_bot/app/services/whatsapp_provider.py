import asyncio
from typing import Any

from app.config.settings import settings
from app.core.logger import log_error, log_event
from app.services import twilio_service, whatsapp_cloud_service

TWILIO_PROVIDER = "twilio"
META_PROVIDER = "meta"
DEFAULT_RETRY_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 1.0


class WhatsAppProviderError(RuntimeError):
    """Raised only after the active WhatsApp provider exhausts safe retries."""


def get_active_provider() -> str:
    """
    Return the configured provider.

    Twilio is the production/testing default until Meta credentials are available.
    Unknown values are treated as Twilio so a bad env value cannot accidentally
    push scheduler jobs to graph.facebook.com.
    """
    provider = (settings.whatsapp_provider or TWILIO_PROVIDER).strip().lower()
    if provider not in {TWILIO_PROVIDER, META_PROVIDER}:
        log_error("Unknown WhatsApp provider configured; falling back to Twilio", configured_provider=provider)
        return TWILIO_PROVIDER
    return provider


async def send_whatsapp_message(to: str, message: str, *, preview_url: bool = False) -> dict[str, Any]:
    """
    Send a text WhatsApp message through the active provider.

    Every app service should call this function instead of importing Twilio or
    Meta directly. That keeps today's Twilio Sandbox flow active while preserving
    the Meta implementation for a future provider switch.
    """
    provider = get_active_provider()
    log_event("whatsapp_provider_selected", provider=provider, message_type="text", to=to)

    if provider == META_PROVIDER:
        return await whatsapp_cloud_service.send_text_message(to, message, preview_url=preview_url)

    return await _send_twilio_with_retry(to, message)


async def send_whatsapp_media(
    to: str,
    media_url: str,
    media_type: str = "document",
    caption: str | None = None,
    filename: str | None = None,
) -> dict[str, Any]:
    """
    Send WhatsApp media through the active provider.

    Twilio Sandbox accepts public media URLs on the Messages API. The caption is
    sent as the message body so users still get useful context beside the file.
    """
    provider = get_active_provider()
    log_event("whatsapp_provider_selected", provider=provider, message_type=media_type, to=to)

    if provider == META_PROVIDER:
        return await whatsapp_cloud_service.send_media_message(
            to=to,
            media_url=media_url,
            media_type=media_type,
            caption=caption,
            filename=filename,
        )

    body = caption or filename or "Please find the requested media attached."
    return await _send_twilio_with_retry(to, body, media_url=media_url)


async def _send_twilio_with_retry(to: str, message: str, media_url: str | None = None) -> dict[str, Any]:
    attempts = max(1, DEFAULT_RETRY_ATTEMPTS)
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            log_event(
                "twilio_send_attempt",
                provider=TWILIO_PROVIDER,
                to=to,
                attempt=attempt,
                has_media=bool(media_url),
            )
            result = await twilio_service.send_whatsapp_message(to, message, media_url=media_url)
            log_event(
                "twilio_send_success",
                provider=TWILIO_PROVIDER,
                to=to,
                attempt=attempt,
                sid=result.get("sid"),
                status=result.get("status"),
            )
            return {"success": True, "provider": TWILIO_PROVIDER, **result}
        except twilio_service.TwilioServiceError as exc:
            last_error = exc
            log_error(
                "twilio_send_failed",
                provider=TWILIO_PROVIDER,
                to=to,
                attempt=attempt,
                error=str(exc),
            )
            if attempt < attempts:
                await asyncio.sleep(RETRY_BACKOFF_SECONDS * attempt)

    raise WhatsAppProviderError(f"Twilio WhatsApp send failed after {attempts} attempts") from last_error


__all__ = [
    "META_PROVIDER",
    "TWILIO_PROVIDER",
    "WhatsAppProviderError",
    "get_active_provider",
    "send_whatsapp_media",
    "send_whatsapp_message",
]
