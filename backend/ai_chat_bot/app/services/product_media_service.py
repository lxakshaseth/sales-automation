import json
import os
from typing import Any

from app.core.logger import log_event
from app.services.whatsapp_cloud_service import send_media_message

DEFAULT_MEDIA_CATALOG = {
    "brochure": {
        "media_type": "document",
        "url": os.getenv("DEFAULT_BROCHURE_URL", ""),
        "caption": "Here is the product brochure.",
        "filename": "brochure.pdf",
    },
    "demo": {
        "media_type": "video",
        "url": os.getenv("DEFAULT_DEMO_VIDEO_URL", ""),
        "caption": "Here is a quick demo video.",
    },
    "product_image": {
        "media_type": "image",
        "url": os.getenv("DEFAULT_PRODUCT_IMAGE_URL", ""),
        "caption": "Here is the product image.",
    },
}


class ProductMediaError(RuntimeError):
    """Raised when requested product media is not available."""


def _load_media_catalog() -> dict[str, dict[str, Any]]:
    raw_catalog = os.getenv("PRODUCT_MEDIA_CATALOG_JSON")
    if not raw_catalog:
        return DEFAULT_MEDIA_CATALOG
    try:
        catalog = json.loads(raw_catalog)
    except json.JSONDecodeError as exc:
        raise ProductMediaError("PRODUCT_MEDIA_CATALOG_JSON is invalid JSON") from exc
    if not isinstance(catalog, dict):
        raise ProductMediaError("PRODUCT_MEDIA_CATALOG_JSON must be an object")
    return catalog


def resolve_media_request(query: str) -> dict[str, Any] | None:
    text = str(query or "").lower()
    if any(token in text for token in ("brochure", "pdf", "catalog", "catalogue")):
        key = "brochure"
    elif any(token in text for token in ("demo", "video", "watch")):
        key = "demo"
    elif any(token in text for token in ("image", "photo", "picture", "product")):
        key = "product_image"
    else:
        return None

    media = _load_media_catalog().get(key) or {}
    if not media.get("url"):
        raise ProductMediaError(f"No media URL configured for {key}")
    return {"key": key, **media}


async def send_product_media(to: str, query: str) -> dict[str, Any]:
    media = resolve_media_request(query)
    if not media:
        return {"success": False, "reason": "no_media_intent"}
    result = await send_media_message(
        to=to,
        media_url=media["url"],
        media_type=media.get("media_type", "document"),
        caption=media.get("caption"),
        filename=media.get("filename"),
    )
    log_event("media_sent", to=to, media_key=media["key"], media_type=media.get("media_type"))
    return {"success": True, "media": media, "delivery": result}
