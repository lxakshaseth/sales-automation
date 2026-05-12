import asyncio

from app.tools.mongo_tool import get_chat_history, save_chat, save_lead, save_summary


async def main() -> None:
    user_id = "demo-user-001"

    conversation = await save_chat(
        user_id=user_id,
        messages=[
            {
                "role": "user",
                "content": "Can your AI agent help my sales team follow up faster?",
            },
            {
                "role": "assistant",
                "content": "Yes. How many leads does your team handle each week?",
            },
        ],
        intents=["lead_qualification", "sales_automation_interest"],
        lead_status="new",
        summary="User is evaluating AI sales follow-up automation.",
        metadata={"channel": "website_chat"},
    )

    await save_summary(
        user_id=user_id,
        conversation_id=conversation["_id"],
        summary="User asked about faster lead follow-up for a sales team.",
        intents=["lead_qualification"],
    )

    await save_lead(
        user_id=user_id,
        lead_status="qualified",
        lead_data={"company_size": "10-25", "use_case": "lead follow-up"},
        intents=["demo_request"],
    )

    history = await get_chat_history(user_id, limit=10)
    print(history)


if __name__ == "__main__":
    asyncio.run(main())
