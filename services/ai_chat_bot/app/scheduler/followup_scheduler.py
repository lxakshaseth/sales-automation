from datetime import datetime
from typing import Any

from app.scheduler.followup import cancel_followup, list_jobs, schedule_followup


async def schedule_sales_followup(
    user_id: str,
    message: str,
    *,
    scheduled_time: datetime | str | None = None,
    delay_seconds: int | float | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Public follow-up scheduler for future CRM, analytics, and human handoff flows.

    It wraps the existing generic scheduler with a sales-specific module name so the
    architecture can grow without changing tool/router call sites.
    """
    return await schedule_followup(
        user_id=user_id,
        message=message,
        scheduled_time=scheduled_time,
        delay_seconds=delay_seconds,
        tool_name="send_whatsapp",
        tool_args={"to": user_id, "message": message, **(metadata or {})},
    )


async def cancel_sales_followup(job_id: str) -> dict[str, Any]:
    return await cancel_followup(job_id)


async def list_scheduled_followups() -> list[dict[str, Any]]:
    return await list_jobs()
