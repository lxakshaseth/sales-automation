import os
import tempfile
from pathlib import Path
from uuid import uuid4

SUPPORTED_MIME_PREFIXES = ("image/", "audio/", "video/")
SUPPORTED_DOCUMENT_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain",
}
DEFAULT_MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024


class FileValidationError(ValueError):
    """Raised when a downloaded media file is unsafe or unsupported."""


def detect_media_type(content_type: str | None) -> str:
    """Map Twilio MIME types to broad media categories used by the AI pipeline."""
    content_type = (content_type or "").split(";")[0].strip().lower()
    if content_type.startswith("image/"):
        return "image"
    if content_type.startswith("audio/"):
        return "audio"
    if content_type.startswith("video/"):
        return "video"
    if content_type in SUPPORTED_DOCUMENT_MIME_TYPES:
        return "document"
    return "unsupported"


def validate_mime_type(content_type: str | None) -> str:
    media_type = detect_media_type(content_type)
    if media_type == "unsupported":
        raise FileValidationError(f"Unsupported media type: {content_type}")
    return media_type


def validate_file_size(file_path: str, max_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES) -> int:
    size = os.path.getsize(file_path)
    if size > max_size_bytes:
        raise FileValidationError(f"File exceeds max size of {max_size_bytes} bytes")
    return size


def generate_unique_filename(content_type: str | None, prefix: str = "twilio_media") -> str:
    extension = content_type_to_extension(content_type)
    return f"{prefix}_{uuid4().hex}{extension}"


def content_type_to_extension(content_type: str | None) -> str:
    mapping = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "audio/mpeg": ".mp3",
        "audio/ogg": ".ogg",
        "audio/wav": ".wav",
        "video/mp4": ".mp4",
        "application/pdf": ".pdf",
        "application/msword": ".doc",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "text/plain": ".txt",
    }
    return mapping.get((content_type or "").split(";")[0].strip().lower(), ".bin")


def temporary_media_path(filename: str) -> str:
    return str(Path(tempfile.gettempdir()) / filename)


def cleanup_temp_file(file_path: str | None) -> None:
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
