import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.config import HUBSPOT_API_KEY

logger = logging.getLogger(__name__)

HUBSPOT_BASE_URL = "https://api.hubapi.com"
DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_BACKOFF_SECONDS = 0.5
LEAD_STAGES = {"new", "interested", "meeting_booked", "converted", "inactive"}

_hubspot_client: httpx.AsyncClient | None = None


class HubSpotCRMError(RuntimeError):
    """Raised when HubSpot CRM operations fail."""


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _split_name(name: str | None) -> tuple[str | None, str | None]:
    if not name or not name.strip():
        return None, None

    parts = name.strip().split(maxsplit=1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else None
    return first_name, last_name


def _clean_properties(properties: dict[str, Any]) -> dict[str, str]:
    """
    HubSpot properties are string-like values.

    Empty values are omitted so we do not accidentally overwrite useful CRM data.
    """
    return {
        key: str(value)
        for key, value in properties.items()
        if value is not None and str(value).strip() != ""
    }


def _normalize_lead_status(lead_status: str | None) -> str:
    original = str(lead_status or "NEW").strip()
    value = original.lower()
    if value in LEAD_STAGES and original.islower():
        return value
    return original


def _structured_response(
    *,
    success: bool,
    action: str,
    data: Any = None,
    error: str | None = None,
    error_type: str | None = None,
    attempts: int = 0,
) -> dict[str, Any]:
    return {
        "success": success,
        "action": action,
        "data": data,
        "error": error,
        "error_type": error_type,
        "attempts": attempts,
        "timestamp": _utc_now(),
    }


def _get_hubspot_client() -> httpx.AsyncClient:
    """
    Reuse one async HTTP client per process.

    httpx.AsyncClient keeps connections pooled, which matters when autonomous
    agents create contacts, add notes, and update lead state in quick succession.
    """
    global _hubspot_client

    if not HUBSPOT_API_KEY:
        raise HubSpotCRMError("HUBSPOT_API_KEY is not configured")

    if _hubspot_client is None:
        _hubspot_client = httpx.AsyncClient(
            base_url=HUBSPOT_BASE_URL,
            timeout=httpx.Timeout(DEFAULT_TIMEOUT_SECONDS),
            headers={
                "Authorization": f"Bearer {HUBSPOT_API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

    return _hubspot_client


async def close_hubspot_client() -> None:
    """Close the shared HubSpot HTTP client during FastAPI shutdown or tests."""
    global _hubspot_client

    if _hubspot_client is not None:
        await _hubspot_client.aclose()
        _hubspot_client = None


async def _request(
    method: str,
    path: str,
    *,
    action: str,
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    retry_attempts: int = DEFAULT_RETRY_ATTEMPTS,
) -> dict[str, Any]:
    attempts = max(1, retry_attempts)
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            response = await _get_hubspot_client().request(method, path, json=json, params=params)
            response.raise_for_status()
            data = response.json() if response.content else {}
            return _structured_response(success=True, action=action, data=data, attempts=attempt)
        except httpx.HTTPStatusError as exc:
            last_error = exc
            status_code = exc.response.status_code
            response_text = exc.response.text
            logger.warning(
                "HubSpot API error: action=%s status=%s attempt=%s/%s body=%s",
                action,
                status_code,
                attempt,
                attempts,
                response_text,
            )
            if status_code not in {429, 500, 502, 503, 504}:
                break
        except httpx.RequestError as exc:
            last_error = exc
            logger.warning("HubSpot request error: action=%s attempt=%s/%s", action, attempt, attempts)

        if attempt < attempts:
            await asyncio.sleep(DEFAULT_RETRY_BACKOFF_SECONDS * attempt)

    logger.error("HubSpot operation failed: action=%s error=%s", action, last_error)
    return _structured_response(
        success=False,
        action=action,
        error=str(last_error),
        error_type=type(last_error).__name__ if last_error else HubSpotCRMError.__name__,
        attempts=attempts,
    )


async def create_lead(
    name: str,
    email: str,
    phone: str | None = None,
    lead_status: str = "NEW",
    ai_summary: str | None = None,
    lead_score: int | None = None,
    recommended_next_action: str | None = None,
) -> dict[str, Any]:
    """
    Create a HubSpot contact for a detected AI chatbot lead.

    AI summaries are stored as timeline notes because most HubSpot accounts do not
    have a default custom contact property for generated summaries.
    """
    first_name, last_name = _split_name(name)
    properties = _clean_properties(
        {
            "email": email,
            "firstname": first_name,
            "lastname": last_name,
            "phone": phone,
            "hs_lead_status": _normalize_lead_status(lead_status),
        }
    )

    response = await _request(
        "POST",
        "/crm/v3/objects/contacts",
        action="create_lead",
        json={"properties": properties},
    )

    if response["success"] and (ai_summary or lead_score is not None or recommended_next_action):
        contact_id = response["data"].get("id")
        note_parts = []
        if ai_summary:
            note_parts.append(f"AI Summary: {ai_summary}")
        if lead_score is not None:
            note_parts.append(f"Lead score: {lead_score}")
        if recommended_next_action:
            note_parts.append(f"Recommended next action: {recommended_next_action}")
        note_response = await add_note(
            contact_id=contact_id,
            note="\n".join(note_parts),
        )
        response["data"]["ai_summary_note"] = note_response

    return response


async def update_customer(
    email: str | None = None,
    contact_id: str | None = None,
    name: str | None = None,
    phone: str | None = None,
    lead_status: str | None = None,
    ai_summary: str | None = None,
) -> dict[str, Any]:
    """Update contact fields by HubSpot record ID or by email."""
    if not email and not contact_id:
        raise ValueError("email or contact_id is required")

    first_name, last_name = _split_name(name)
    properties = _clean_properties(
        {
            "firstname": first_name,
            "lastname": last_name,
            "phone": phone,
            "hs_lead_status": _normalize_lead_status(lead_status) if lead_status else None,
        }
    )

    path = f"/crm/v3/objects/contacts/{contact_id or email}"
    params = None if contact_id else {"idProperty": "email"}
    response = await _request(
        "PATCH",
        path,
        action="update_customer",
        json={"properties": properties},
        params=params,
    )

    if response["success"] and ai_summary:
        resolved_contact_id = response["data"].get("id") or contact_id
        note_response = await add_note(
            contact_id=resolved_contact_id,
            note=f"AI Summary: {ai_summary}",
        )
        response["data"]["ai_summary_note"] = note_response

    return response


async def add_note(
    note: str,
    contact_id: str | None = None,
    email: str | None = None,
) -> dict[str, Any]:
    """Add an AI-generated note to a HubSpot contact timeline."""
    if not contact_id and not email:
        raise ValueError("contact_id or email is required")

    if not contact_id:
        contact_response = await get_contact(email=email)
        if not contact_response["success"]:
            return contact_response
        contact_id = contact_response["data"].get("id")

    payload = {
        "properties": {
            "hs_note_body": note,
            "hs_timestamp": _utc_now(),
        },
        "associations": [
            {
                "to": {"id": contact_id},
                "types": [
                    {
                        "associationCategory": "HUBSPOT_DEFINED",
                        "associationTypeId": 202,
                    }
                ],
            }
        ],
    }

    return await _request("POST", "/crm/v3/objects/notes", action="add_note", json=payload)


async def get_contact(email: str | None = None, contact_id: str | None = None) -> dict[str, Any]:
    """Fetch a contact by email or HubSpot contact ID."""
    if not email and not contact_id:
        raise ValueError("email or contact_id is required")

    path = f"/crm/v3/objects/contacts/{contact_id or email}"
    params = {
        "properties": "email,firstname,lastname,phone,hs_lead_status,createdate,lastmodifieddate"
    }
    if not contact_id:
        params["idProperty"] = "email"

    return await _request("GET", path, action="get_contact", params=params)


async def update_lead_status(
    lead_status: str,
    email: str | None = None,
    contact_id: str | None = None,
    ai_summary: str | None = None,
) -> dict[str, Any]:
    """Update lead status and optionally attach the AI summary that caused the change."""
    return await update_customer(
        email=email,
        contact_id=contact_id,
        lead_status=lead_status,
        ai_summary=ai_summary,
    )
