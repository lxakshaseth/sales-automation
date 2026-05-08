import asyncio
import logging
from typing import Any

import cloudinary.uploader

from app.config.cloudinary_config import configure_cloudinary
from app.utils.file_utils import detect_media_type, validate_file_size, validate_mime_type

logger = logging.getLogger(__name__)


class MediaUploadError(RuntimeError):
    """Raised when media cannot be uploaded to Cloudinary."""


def _normalize_upload_response(response: dict[str, Any], media_type: str) -> dict[str, Any]:
    return {
        "secure_url": response.get("secure_url"),
        "public_id": response.get("public_id"),
        "resource_type": response.get("resource_type"),
        "format": response.get("format"),
        "media_type": media_type,
        "bytes": response.get("bytes"),
        "original_filename": response.get("original_filename"),
    }


async def upload_any_file(
    file_path: str,
    *,
    content_type: str | None = None,
    folder: str = "twilio_whatsapp_media",
    user_id: str | None = None,
) -> dict[str, Any]:
    """
    Upload any supported WhatsApp media to Cloudinary.

    Cloudinary SDK uploads are synchronous, so this function runs them in a worker
    thread while preserving async-compatible FastAPI architecture.
    """
    media_type = validate_mime_type(content_type)
    file_size = validate_file_size(file_path)

    def _upload() -> dict[str, Any]:
        configure_cloudinary()
        return cloudinary.uploader.upload(
            file_path,
            resource_type="auto",
            folder=folder,
            tags=["twilio", "whatsapp", media_type],
            context={
                "source": "twilio_whatsapp",
                "user_id": user_id or "",
                "media_type": media_type,
                "content_type": content_type or "",
            },
        )

    try:
        response = await asyncio.to_thread(_upload)
    except Exception as exc:
        logger.exception("Cloudinary upload failed media_type=%s content_type=%s", media_type, content_type)
        raise MediaUploadError("Cloudinary upload failed") from exc

    normalized = _normalize_upload_response(response, media_type)
    normalized["local_file_size"] = file_size
    logger.info("Cloudinary upload success public_id=%s media_type=%s", normalized["public_id"], media_type)
    return normalized


async def upload_image(file_path: str, content_type: str | None = "image/jpeg", **kwargs) -> dict[str, Any]:
    return await upload_any_file(file_path, content_type=content_type, **kwargs)


async def upload_audio(file_path: str, content_type: str | None = "audio/mpeg", **kwargs) -> dict[str, Any]:
    return await upload_any_file(file_path, content_type=content_type, **kwargs)


async def upload_video(file_path: str, content_type: str | None = "video/mp4", **kwargs) -> dict[str, Any]:
    return await upload_any_file(file_path, content_type=content_type, **kwargs)


async def upload_document(file_path: str, content_type: str | None = "application/pdf", **kwargs) -> dict[str, Any]:
    return await upload_any_file(file_path, content_type=content_type, **kwargs)


def describe_media_for_ai(uploaded_media: list[dict[str, Any]]) -> str:
    """Build a compact summary for the Groq reply service and future AI processors."""
    if not uploaded_media:
        return ""

    parts = []
    for item in uploaded_media:
        media_type = item.get("media_type") or detect_media_type(item.get("content_type"))
        parts.append(f"{media_type}: {item.get('secure_url')}")
    return "User attached media - " + "; ".join(parts)
