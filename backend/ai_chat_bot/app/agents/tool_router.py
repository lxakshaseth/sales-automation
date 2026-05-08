from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.logger import log_event
from app.core.tool_router import execute_tool, list_tools, register_tool
from app.scheduler.followup import schedule_reminder
from app.services.product_media_service import send_product_media
from app.services.whatsapp_cloud_service import send_media_message, send_text_message
from app.tools.calendar_tool import book_meeting, check_availability, get_upcoming_events


async def send_whatsapp(to: str, message: str) -> dict[str, Any]:
    return await send_text_message(to, message)


async def send_media(to: str, media_url: str | None = None, media_type: str = "document", caption: str | None = None, query: str | None = None) -> dict[str, Any]:
    if query:
        return await send_product_media(to, query)
    if not media_url:
        raise ValueError("media_url or query is required")
    return await send_media_message(to=to, media_url=media_url, media_type=media_type, caption=caption)


async def schedule_meeting(
    user_id: str,
    title: str,
    start_time: str,
    end_time: str,
    attendees: list[str] | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    result = await book_meeting(
        user_id=user_id,
        title=title,
        start_time=start_time,
        end_time=end_time,
        attendees=attendees,
        description=description,
        schedule_reminder_minutes_before=5,
    )
    if result.get("success"):
        log_event("meeting_booked", user_id=user_id, event=result.get("data", {}))
    return result


async def calendar_checker(user_id: str, max_results: int = 10) -> dict[str, Any]:
    availability = await check_availability(user_id=user_id, max_slots=3)
    if availability.get("success"):
        return availability
    return await get_upcoming_events(user_id=user_id, max_results=max_results)


async def reminder_scheduler(user_id: str, message: str, delay_minutes: float = 5, job_id: str | None = None) -> dict[str, Any]:
    run_at = datetime.now(timezone.utc) + timedelta(minutes=float(delay_minutes))
    return await schedule_reminder(
        user_id=user_id,
        message=message,
        scheduled_time=run_at,
        job_id=job_id,
        tool_name="send_whatsapp",
        tool_args={"to": user_id, "message": message},
    )


def register_agent_tools() -> None:
    register_tool("send_whatsapp", send_whatsapp, "Send a WhatsApp Cloud API text message.", timeout_seconds=15, retries=1)
    register_tool("send_media", send_media, "Send image, video, or document media over WhatsApp.", timeout_seconds=20, retries=1)
    register_tool("schedule_meeting", schedule_meeting, "Create a Google Calendar meeting with a Google Meet link.", timeout_seconds=25, retries=1)
    register_tool("calendar_checker", calendar_checker, "Check upcoming Google Calendar events.", timeout_seconds=10, retries=1)
    register_tool("reminder_scheduler", reminder_scheduler, "Schedule a WhatsApp reminder via APScheduler.", timeout_seconds=10, retries=1)


register_agent_tools()

__all__ = ["execute_tool", "list_tools", "register_agent_tools"]
