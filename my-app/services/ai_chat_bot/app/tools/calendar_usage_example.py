import asyncio

from app.tools.calendar_tool import book_meeting, get_upcoming_events, reschedule_meeting


async def ai_booking_workflow() -> None:
    # 1. AI detects booking intent and extracts date/time from the chat.
    booking = await book_meeting(
        user_id="demo-user-001",
        title="Sales automation discovery call",
        start_time="2026-05-08T10:00:00+05:30",
        end_time="2026-05-08T10:30:00+05:30",
        attendees=["lead@example.com"],
        description="Booked by the AI chatbot after lead qualification.",
        send_confirmation=True,
        schedule_reminder_minutes_before=30,
    )

    # 2. Agent can inspect upcoming calendar context before booking more meetings.
    upcoming = await get_upcoming_events(user_id="demo-user-001", max_results=5)

    # 3. If the user asks to move the meeting, the AI can reschedule it.
    event_id = booking.get("data", {}).get("event_id")
    if event_id:
        await reschedule_meeting(
            user_id="demo-user-001",
            event_id=event_id,
            start_time="2026-05-08T11:00:00+05:30",
            end_time="2026-05-08T11:30:00+05:30",
        )

    print({"booking": booking, "upcoming": upcoming})


if __name__ == "__main__":
    asyncio.run(ai_booking_workflow())
