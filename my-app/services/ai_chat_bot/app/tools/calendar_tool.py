import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import httpx

from app.core.config import (
    GOOGLE_ACCESS_TOKEN,
    GOOGLE_CALENDAR_ID,
    GOOGLE_CALENDAR_TIMEZONE,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REFRESH_TOKEN,
)
from app.tools.email_tool import send_email

logger = logging.getLogger(__name__)

GOOGLE_CALENDAR_BASE_URL = "https://www.googleapis.com/calendar/v3"
GOOGLE_OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_BACKOFF_SECONDS = 0.5
DEFAULT_TIMEOUT_SECONDS = 10.0

_calendar_client: httpx.AsyncClient | None = None
_oauth_client: httpx.AsyncClient | None = None
_access_token: str | None = GOOGLE_ACCESS_TOKEN


class CalendarToolError(RuntimeError):
    """Raised when Google Calendar booking operations fail."""


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _parse_datetime(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)

    return parsed


def _to_rfc3339(value: datetime | str) -> str:
    return _parse_datetime(value).isoformat()


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


def _get_calendar_client() -> httpx.AsyncClient:
    """Reuse one async Calendar API client per process for connection pooling."""
    global _calendar_client

    if _calendar_client is None:
        _calendar_client = httpx.AsyncClient(
            base_url=GOOGLE_CALENDAR_BASE_URL,
            timeout=httpx.Timeout(DEFAULT_TIMEOUT_SECONDS),
            headers={"Accept": "application/json"},
        )

    return _calendar_client


def _get_oauth_client() -> httpx.AsyncClient:
    """Separate OAuth client because token refresh uses a different base URL."""
    global _oauth_client

    if _oauth_client is None:
        _oauth_client = httpx.AsyncClient(timeout=httpx.Timeout(DEFAULT_TIMEOUT_SECONDS))

    return _oauth_client


async def close_calendar_client() -> None:
    """Close shared HTTP clients during FastAPI shutdown or tests."""
    global _calendar_client, _oauth_client

    if _calendar_client is not None:
        await _calendar_client.aclose()
        _calendar_client = None

    if _oauth_client is not None:
        await _oauth_client.aclose()
        _oauth_client = None


async def _refresh_access_token() -> str:
    """Refresh OAuth access token from long-lived refresh token credentials."""
    global _access_token

    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET or not GOOGLE_REFRESH_TOKEN:
        raise CalendarToolError("Google OAuth credentials are not configured")

    response = await _get_oauth_client().post(
        GOOGLE_OAUTH_TOKEN_URL,
        data={
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "refresh_token": GOOGLE_REFRESH_TOKEN,
            "grant_type": "refresh_token",
        },
    )
    response.raise_for_status()
    token_data = response.json()
    _access_token = token_data["access_token"]
    return _access_token


async def _get_access_token() -> str:
    if _access_token:
        return _access_token

    return await _refresh_access_token()


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
            token = await _get_access_token()
            response = await _get_calendar_client().request(
                method,
                path,
                json=json,
                params=params,
                headers={"Authorization": f"Bearer {token}"},
            )

            if response.status_code == 401:
                token = await _refresh_access_token()
                response = await _get_calendar_client().request(
                    method,
                    path,
                    json=json,
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                )

            response.raise_for_status()
            data = response.json() if response.content else {}
            return _structured_response(success=True, action=action, data=data, attempts=attempt)
        except httpx.HTTPStatusError as exc:
            last_error = exc
            status_code = exc.response.status_code
            logger.warning(
                "Google Calendar API error: action=%s status=%s attempt=%s/%s body=%s",
                action,
                status_code,
                attempt,
                attempts,
                exc.response.text,
            )
            if status_code not in {429, 500, 502, 503, 504}:
                break
        except (httpx.RequestError, CalendarToolError, KeyError) as exc:
            last_error = exc
            logger.warning("Google Calendar request error: action=%s attempt=%s/%s", action, attempt, attempts)

        if attempt < attempts:
            await asyncio.sleep(DEFAULT_RETRY_BACKOFF_SECONDS * attempt)

    logger.error("Google Calendar operation failed: action=%s error=%s", action, last_error)
    return _structured_response(
        success=False,
        action=action,
        error=str(last_error),
        error_type=type(last_error).__name__ if last_error else CalendarToolError.__name__,
        attempts=attempts,
    )


def _event_payload(
    *,
    user_id: str,
    title: str,
    start_time: datetime | str,
    end_time: datetime | str,
    attendees: list[str] | None = None,
    description: str | None = None,
    timezone_name: str = GOOGLE_CALENDAR_TIMEZONE,
    create_meet_link: bool = True,
) -> dict[str, Any]:
    if not user_id or not str(user_id).strip():
        raise ValueError("user_id is required")

    if not title or not title.strip():
        raise ValueError("title is required")

    payload: dict[str, Any] = {
        "summary": title,
        "description": description or f"Booked by AI chatbot for user_id={user_id}",
        "start": {"dateTime": _to_rfc3339(start_time), "timeZone": timezone_name},
        "end": {"dateTime": _to_rfc3339(end_time), "timeZone": timezone_name},
        "attendees": [{"email": email} for email in attendees or []],
        "extendedProperties": {
            "private": {
                "user_id": str(user_id),
                "source": "agentic_ai_chatbot",
            }
        },
    }

    if create_meet_link:
        payload["conferenceData"] = {
            "createRequest": {
                "requestId": f"meet-{uuid4().hex}",
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        }

    return payload


def _extract_event_summary(user_id: str, event: dict[str, Any]) -> dict[str, Any]:
    return {
        "user_id": user_id,
        "event_id": event.get("id"),
        "title": event.get("summary"),
        "start_time": event.get("start", {}).get("dateTime"),
        "end_time": event.get("end", {}).get("dateTime"),
        "attendees": [attendee.get("email") for attendee in event.get("attendees", [])],
        "meeting_link": event.get("hangoutLink"),
        "html_link": event.get("htmlLink"),
    }


async def create_event(
    user_id: str,
    title: str,
    start_time: datetime | str,
    end_time: datetime | str,
    attendees: list[str] | None = None,
    description: str | None = None,
    calendar_id: str = GOOGLE_CALENDAR_ID,
    create_meet_link: bool = True,
    send_updates: str = "all",
) -> dict[str, Any]:
    """Create a Google Calendar event with optional Google Meet conference data."""
    payload = _event_payload(
        user_id=user_id,
        title=title,
        start_time=start_time,
        end_time=end_time,
        attendees=attendees,
        description=description,
        create_meet_link=create_meet_link,
    )
    response = await _request(
        "POST",
        f"/calendars/{calendar_id}/events",
        action="create_event",
        json=payload,
        params={"conferenceDataVersion": 1, "sendUpdates": send_updates},
    )

    if response["success"]:
        response["data"] = _extract_event_summary(user_id, response["data"])

    return response


async def _schedule_calendar_reminder(
    *,
    user_id: str,
    message: str,
    scheduled_time: datetime,
    event_id: str,
    meeting_link: str | None,
    attendees: list[str],
) -> dict[str, Any]:
    """Lazy wrapper avoids importing the scheduler while calendar module loads."""
    from app.scheduler.followup import schedule_reminder

    return await schedule_reminder(
        user_id=user_id,
        message=message,
        scheduled_time=scheduled_time,
        job_id=f"calendar-reminder:{event_id}",
        task_type="calendar_reminder",
        extra_metadata={
            "event_id": event_id,
            "meeting_link": meeting_link,
            "attendees": attendees,
        },
    )


async def book_meeting(
    user_id: str,
    title: str,
    start_time: datetime | str,
    end_time: datetime | str,
    attendees: list[str] | None = None,
    description: str | None = None,
    calendar_id: str = GOOGLE_CALENDAR_ID,
    send_confirmation: bool = True,
    schedule_reminder_minutes_before: int | None = 30,
) -> dict[str, Any]:
    """
    Book a meeting, send confirmation, and optionally schedule an autonomous reminder.
    """
    response = await create_event(
        user_id=user_id,
        title=title,
        start_time=start_time,
        end_time=end_time,
        attendees=attendees,
        description=description,
        calendar_id=calendar_id,
    )

    if not response["success"]:
        return response

    event = response["data"]
    confirmations = []
    if send_confirmation:
        for attendee in attendees or []:
            confirmations.append(
                await send_email(
                    attendee,
                    f"Meeting confirmed: {title}",
                    f"Your meeting is confirmed for {event['start_time']}. Link: {event.get('meeting_link') or event.get('html_link')}",
                )
            )

    reminder = None
    if schedule_reminder_minutes_before is not None:
        reminder_time = _parse_datetime(start_time) - timedelta(minutes=schedule_reminder_minutes_before)
        reminder = await _schedule_calendar_reminder(
            user_id=user_id,
            message=f"Reminder: {title} starts at {event['start_time']}",
            scheduled_time=reminder_time,
            event_id=event["event_id"],
            meeting_link=event.get("meeting_link"),
            attendees=attendees or [],
        )

    response["data"]["confirmation_sent"] = bool(confirmations)
    response["data"]["confirmations"] = confirmations
    response["data"]["reminder"] = reminder
    return response


async def cancel_meeting(
    user_id: str,
    event_id: str,
    calendar_id: str = GOOGLE_CALENDAR_ID,
    send_updates: str = "all",
) -> dict[str, Any]:
    """Cancel a Google Calendar event."""
    if not event_id or not event_id.strip():
        raise ValueError("event_id is required")

    response = await _request(
        "DELETE",
        f"/calendars/{calendar_id}/events/{event_id}",
        action="cancel_meeting",
        params={"sendUpdates": send_updates},
    )

    if response["success"]:
        response["data"] = {"user_id": user_id, "event_id": event_id, "cancelled": True}

    return response


async def reschedule_meeting(
    user_id: str,
    event_id: str,
    start_time: datetime | str,
    end_time: datetime | str,
    calendar_id: str = GOOGLE_CALENDAR_ID,
    send_updates: str = "all",
    schedule_reminder_minutes_before: int | None = 30,
) -> dict[str, Any]:
    """Move a meeting to a new start/end time and refresh its reminder."""
    if not event_id or not event_id.strip():
        raise ValueError("event_id is required")

    payload = {
        "start": {"dateTime": _to_rfc3339(start_time), "timeZone": GOOGLE_CALENDAR_TIMEZONE},
        "end": {"dateTime": _to_rfc3339(end_time), "timeZone": GOOGLE_CALENDAR_TIMEZONE},
    }
    response = await _request(
        "PATCH",
        f"/calendars/{calendar_id}/events/{event_id}",
        action="reschedule_meeting",
        json=payload,
        params={"conferenceDataVersion": 1, "sendUpdates": send_updates},
    )

    if response["success"]:
        response["data"] = _extract_event_summary(user_id, response["data"])
        if schedule_reminder_minutes_before is not None:
            reminder_time = _parse_datetime(start_time) - timedelta(minutes=schedule_reminder_minutes_before)
            response["data"]["reminder"] = await _schedule_calendar_reminder(
                user_id=user_id,
                message=f"Reminder: {response['data']['title']} starts at {response['data']['start_time']}",
                scheduled_time=reminder_time,
                event_id=event_id,
                meeting_link=response["data"].get("meeting_link"),
                attendees=response["data"].get("attendees", []),
            )

    return response


async def get_upcoming_events(
    user_id: str,
    calendar_id: str = GOOGLE_CALENDAR_ID,
    max_results: int = 10,
    time_min: datetime | str | None = None,
) -> dict[str, Any]:
    """Fetch upcoming events for booking context and agent planning."""
    params = {
        "timeMin": _to_rfc3339(time_min or datetime.now(UTC)),
        "maxResults": max(1, min(max_results, 50)),
        "singleEvents": "true",
        "orderBy": "startTime",
    }
    response = await _request(
        "GET",
        f"/calendars/{calendar_id}/events",
        action="get_upcoming_events",
        params=params,
    )

    if response["success"]:
        response["data"] = {
            "user_id": user_id,
            "events": [_extract_event_summary(user_id, event) for event in response["data"].get("items", [])],
        }

    return response


async def check_availability(
    user_id: str,
    duration_minutes: int = 30,
    max_slots: int = 3,
    calendar_id: str = GOOGLE_CALENDAR_ID,
) -> dict[str, Any]:
    """
    Return simple candidate free slots for the meeting workflow.

    This keeps the agent useful even before a full scheduling UI exists. The
    workflow checks upcoming events and proposes near-future business-hour slots
    that do not overlap visible calendar events.
    """
    events_response = await get_upcoming_events(user_id=user_id, calendar_id=calendar_id, max_results=20)
    if not events_response["success"]:
        return events_response

    busy = []
    for event in events_response["data"].get("events", []):
        if event.get("start_time") and event.get("end_time"):
            busy.append((_parse_datetime(event["start_time"]), _parse_datetime(event["end_time"])))

    slots = []
    cursor = datetime.now(UTC).replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    while len(slots) < max(1, max_slots):
        if 9 <= cursor.hour < 18:
            end = cursor + timedelta(minutes=duration_minutes)
            overlaps = any(cursor < busy_end and end > busy_start for busy_start, busy_end in busy)
            if not overlaps:
                slots.append({"start_time": cursor.isoformat(), "end_time": end.isoformat()})
        cursor += timedelta(minutes=30)
        if cursor > datetime.now(UTC) + timedelta(days=7):
            break

    return _structured_response(
        success=True,
        action="check_availability",
        data={"user_id": user_id, "available_slots": slots},
        attempts=1,
    )
