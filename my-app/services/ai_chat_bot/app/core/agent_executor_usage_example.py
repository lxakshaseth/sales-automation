import asyncio

from app.core.agent_executor import execute_agent_action


async def main() -> None:
    examples = [
        "Email akshat@example.com and say the meeting is confirmed.",
        "Remember that user-123 wants a WhatsApp follow-up tomorrow.",
        "Create a lead for Akshat Seth at akshat@example.com.",
        "Book a demo for user-123 with lead@example.com tomorrow from 10 to 10:30.",
    ]

    for message in examples:
        result = await execute_agent_action(
            message,
            context={"user_id": "user-123", "timezone": "Asia/Kolkata"},
        )
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
