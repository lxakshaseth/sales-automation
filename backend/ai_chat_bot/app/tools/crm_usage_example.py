import asyncio

from app.tools.crm_tool import add_note, create_lead, update_lead_status
from app.tools.mongo_tool import save_summary


async def ai_lead_workflow() -> None:
    # 1. AI detects lead intent from the chatbot conversation.
    lead = await create_lead(
        name="Akshat Seth",
        email="akshat@example.com",
        phone="+919999999999",
        lead_status="NEW",
        ai_summary="Interested in automating lead follow-ups from chatbot conversations.",
    )

    # 2. AI stores a conversation summary locally for analytics and memory.
    await save_summary(
        user_id="demo-user-001",
        summary="Lead asked about sales automation and follow-up workflows.",
        intents=["lead_intent", "follow_up_request"],
    )

    # 3. Lead status updates automatically after qualification.
    contact_id = lead.get("data", {}).get("id")
    await update_lead_status(
        contact_id=contact_id,
        lead_status="QUALIFIED",
        ai_summary="User is qualified and should receive a CRM follow-up.",
    )

    await add_note(
        contact_id=contact_id,
        note="AI workflow completed: contact created, summary stored, status updated.",
    )


if __name__ == "__main__":
    asyncio.run(ai_lead_workflow())
