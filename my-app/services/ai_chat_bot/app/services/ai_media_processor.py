from typing import Any


async def prepare_media_context(uploaded_media: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Placeholder media AI pipeline.

    Future expansion points:
    - OCR for images and PDFs
    - speech-to-text for audio and voice notes
    - vision AI for screenshots/product photos
    - RAG document ingestion for PDFs and docs
    """
    return {
        "media_count": len(uploaded_media),
        "items": [
            {
                "media_type": item.get("media_type"),
                "secure_url": item.get("secure_url"),
                "public_id": item.get("public_id"),
                "format": item.get("format"),
            }
            for item in uploaded_media
        ],
    }
