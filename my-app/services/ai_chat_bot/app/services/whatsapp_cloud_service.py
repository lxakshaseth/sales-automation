import asyncio
import hashlib
import hmac
from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import Request

from app.core.config import (
    META_APP_SECRET,
    WHATSAPP_ACCESS_TOKEN,
    WHATSAPP_GRAPH_API_VERSION,
    WHATSAPP_GRAPH_BASE_URL,
    WHATSAPP_PHONE_NUMBER_ID,
    WHATSAPP_SEND_RETRY_ATTEMPTS,
    WHATSAPP_WEBHOOK_SIGNATURE_REQUIRED,
)
from app.core.logger import log_error, log_event

DEFAULT_TIMEOUT_SECONDS = 10.0
RETRY_BACKOFF_SECONDS = 0.75

_client: httpx.AsyncClient | None = None


class WhatsAppCloudError(RuntimeError):
    """Raised when WhatsApp Cloud API operations fail."""


@dataclass(frozen=True)
class CloudMessage:
    message_id: str
    from_number: str
    body: str
    message_type: str = "text"
    media_id: str | None = None
    media_mime_type: str | None = None
    media_caption: str | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=f"{WHATSAPP_GRAPH_BASE_URL}/{WHATSAPP_GRAPH_API_VERSION}",
            timeout=httpx.Timeout(DEFAULT_TIMEOUT_SECONDS),
            headers={"Accept": "application/json"},
        )
    return _client


async def close_whatsapp_cloud_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def missing_whatsapp_cloud_values() -> list[str]:
    missing = []
    if not WHATSAPP_ACCESS_TOKEN:
        missing.append("WHATSAPP_ACCESS_TOKEN")
    if not WHATSAPP_PHONE_NUMBER_ID:
        missing.append("WHATSAPP_PHONE_NUMBER_ID")
    return missing


def verify_webhook_token(mode: str | None, token: str | None, challenge: str | None, expected_token: str | None) -> str | None:
    if mode == "subscribe" and token and expected_token and hmac.compare_digest(token, expected_token):
        return challenge or ""
    return None


def verify_meta_signature(raw_body: bytes, signature_header: str | None) -> bool:
    """
    Validate Meta's X-Hub-Signature-256 header.

    If META_APP_SECRET is absent and signatures are not required, the webhook can
    still run in local development.
    """
    if not META_APP_SECRET:
        return not WHATSAPP_WEBHOOK_SIGNATURE_REQUIRED
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(META_APP_SECRET.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def parse_incoming_messages(payload: dict[str, Any]) -> list[CloudMessage]:
    """Extract text and media messages from a WhatsApp Cloud API webhook payload."""
    messages: list[CloudMessage] = []
    for entry in payload.get("entry", []) or []:
        for change in entry.get("changes", []) or []:
            value = change.get("value") or {}
            for message in value.get("messages", []) or []:
                message_type = message.get("type") or "unknown"
                text = ""
                media_id = None
                media_mime_type = None
                media_caption = None
                if message_type == "text":
                    text = (message.get("text") or {}).get("body") or ""
                elif message_type in {"image", "video", "audio", "document"}:
                    media = message.get(message_type) or {}
                    media_id = media.get("id")
                    media_mime_type = media.get("mime_type")
                    media_caption = media.get("caption") or media.get("filename")
                    text = media_caption or f"[{message_type} received]"
                else:
                    text = f"[{message_type} message received]"

                messages.append(
                    CloudMessage(
                        message_id=message.get("id") or "",
                        from_number=message.get("from") or "",
                        body=text,
                        message_type=message_type,
                        media_id=media_id,
                        media_mime_type=media_mime_type,
                        media_caption=media_caption,
                    )
                )
    return [message for message in messages if message.from_number and message.message_id]


async def _post_message(payload: dict[str, Any], action: str) -> dict[str, Any]:
    missing = missing_whatsapp_cloud_values()
    if missing:
        raise WhatsAppCloudError(f"Missing WhatsApp Cloud API configuration: {', '.join(missing)}")

    attempts = max(1, WHATSAPP_SEND_RETRY_ATTEMPTS)
    last_error: Exception | None = None
    path = f"/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    for attempt in range(1, attempts + 1):
        try:
            response = await _get_client().post(path, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            log_event(action, to=payload.get("to"), message_id=(data.get("messages") or [{}])[0].get("id"), attempt=attempt)
            return {"success": True, "action": action, "data": data, "attempts": attempt}
        except httpx.HTTPStatusError as exc:
            last_error = exc
            status_code = exc.response.status_code
            log_error(
                "WhatsApp Cloud API returned an error",
                action=action,
                status_code=status_code,
                body=exc.response.text,
                attempt=attempt,
            )
            if status_code not in {408, 429, 500, 502, 503, 504}:
                break
        except httpx.RequestError as exc:
            last_error = exc
            log_error("WhatsApp Cloud API request failed", action=action, error_type=type(exc).__name__, attempt=attempt)

        if attempt < attempts:
            await asyncio.sleep(RETRY_BACKOFF_SECONDS * attempt)

    raise WhatsAppCloudError(f"{action} failed: {last_error}") from last_error


async def send_text_message(to: str, text: str, preview_url: bool = False) -> dict[str, Any]:
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": str(to).replace("whatsapp:", "").replace("+", ""),
        "type": "text",
        "text": {"preview_url": preview_url, "body": text},
    }
    return await _post_message(payload, "whatsapp_text_sent")


async def send_media_message(
    to: str,
    media_url: str,
    media_type: str,
    caption: str | None = None,
    filename: str | None = None,
) -> dict[str, Any]:
    normalized_type = media_type if media_type in {"image", "video", "audio", "document"} else "document"
    media_payload: dict[str, Any] = {"link": media_url}
    if caption and normalized_type in {"image", "video", "document"}:
        media_payload["caption"] = caption
    if filename and normalized_type == "document":
        media_payload["filename"] = filename
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": str(to).replace("whatsapp:", "").replace("+", ""),
        "type": normalized_type,
        normalized_type: media_payload,
    }
    return await _post_message(payload, "whatsapp_media_sent")


async def read_json_body(request: Request) -> tuple[bytes, dict[str, Any]]:
    raw_body = await request.body()
    try:
        payload = await request.json()
    except Exception as exc:
        raise WhatsAppCloudError("Invalid JSON webhook payload") from exc
    return raw_body, payload
