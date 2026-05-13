"""
Example usage for the autonomous conversation lifecycle services.

This file is intentionally not imported by FastAPI. Run the API normally and the
Twilio webhook will call these services automatically for every inbound user.
"""

from app.services.conversation_service import (
    get_conversation_state,
    record_assistant_message,
    record_message_received,
)
from app.services.owner_settings_service import add_owner_email, get_active_owner_emails


async def example_lifecycle_flow() -> dict:
    user_id = "whatsapp:+15551234567"

    await add_owner_email("owner@example.com")
    await record_message_received(
        user_id=user_id,
        phone_number=user_id,
        message="I need an AI sales chatbot for my website.",
    )
    await record_assistant_message(
        user_id,
        "Great. What industry are you in, and do you want WhatsApp, website chat, or both?",
    )

    return {
        "state": await get_conversation_state(user_id),
        "owner_emails": await get_active_owner_emails(),
    }
