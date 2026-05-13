import logging
from typing import Any

import aiofiles
import httpx

from app.config.settings import settings
from app.services.media_service import upload_any_file
from app.utils.file_utils import cleanup_temp_file, generate_unique_filename, temporary_media_path, validate_mime_type

logger = logging.getLogger(__name__)


class WhatsAppMediaError(RuntimeError):
    """Raised when Twilio media cannot be downloaded or uploaded."""


async def download_twilio_media(media_url: str, content_type: str, message_sid: str) -> str:
    """
    Download Twilio-hosted media to a temporary file.

    Twilio media URLs may require account SID/auth token basic auth. The temp file
    is deleted after Cloudinary upload in `process_twilio_media`.
    """
    validate_mime_type(content_type)
    filename = generate_unique_filename(content_type, prefix=f"twilio_{message_sid}")
    file_path = temporary_media_path(filename)
    auth = None
    if settings.twilio_account_sid and settings.twilio_auth_token:
        auth = (settings.twilio_account_sid, settings.twilio_auth_token)

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(media_url, auth=auth, follow_redirects=True)
            response.raise_for_status()

        async with aiofiles.open(file_path, "wb") as file:
            await file.write(response.content)
    except Exception as exc:
        cleanup_temp_file(file_path)
        logger.exception("Failed to download Twilio media message_sid=%s media_url=%s", message_sid, media_url)
        raise WhatsAppMediaError("Failed to download Twilio media") from exc

    return file_path


async def process_twilio_media(
    *,
    media_url: str,
    content_type: str,
    message_sid: str,
    user_id: str,
) -> dict[str, Any]:
    """
    Twilio media flow:
    download temp file -> upload to Cloudinary -> cleanup temp file -> return metadata.
    """
    temp_path = None
    try:
        temp_path = await download_twilio_media(media_url, content_type, message_sid)
        uploaded = await upload_any_file(temp_path, content_type=content_type, user_id=user_id)
        uploaded["source_url"] = media_url
        uploaded["content_type"] = content_type
        uploaded["message_sid"] = message_sid
        logger.info("WhatsApp media processed message_sid=%s public_id=%s", message_sid, uploaded.get("public_id"))
        return uploaded
    except Exception as exc:
        logger.exception("WhatsApp media processing failed message_sid=%s content_type=%s", message_sid, content_type)
        raise WhatsAppMediaError("Failed to process WhatsApp media") from exc
    finally:
        cleanup_temp_file(temp_path)


async def process_all_twilio_media(form_data: dict[str, Any], *, message_sid: str, user_id: str) -> list[dict[str, Any]]:
    """Process all MediaUrlN / MediaContentTypeN values from a Twilio webhook."""
    media_count = int(form_data.get("NumMedia") or 0)
    uploaded_media = []

    for index in range(media_count):
        media_url = str(form_data.get(f"MediaUrl{index}", "")).strip()
        content_type = str(form_data.get(f"MediaContentType{index}", "")).strip()
        if not media_url or not content_type:
            logger.warning("Skipping incomplete Twilio media index=%s message_sid=%s", index, message_sid)
            continue

        uploaded_media.append(
            await process_twilio_media(
                media_url=media_url,
                content_type=content_type,
                message_sid=message_sid,
                user_id=user_id,
            )
        )

    return uploaded_media
