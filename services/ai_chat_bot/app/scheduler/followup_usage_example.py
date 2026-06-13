import asyncio

from app.scheduler.followup import (
    cancel_followup,
    list_jobs,
    schedule_24h_no_reply_followup,
    schedule_reminder,
)


async def example_no_reply_workflow() -> None:
    followup = await schedule_24h_no_reply_followup(
        user_id="demo-user-001",
        message="Just checking in. Do you still want help with sales automation?",
    )

    reminder = await schedule_reminder(
        user_id="demo-user-001",
        message="Prepare CRM follow-up summary before the sales call.",
        delay_seconds=60 * 60,
    )

    print(await list_jobs())
    await cancel_followup(reminder["job_id"])
    print(followup)


if __name__ == "__main__":
    asyncio.run(example_no_reply_workflow())
