import asyncio

from app.core.rate_limiter import check_rate_limit, check_tool_rate_limit, reset_limit


async def main() -> None:
    user_check = await check_rate_limit("demo-user-001", scope="user", limit_type="message")
    email_check = await check_tool_rate_limit("demo-user-001", "send_email")

    if user_check["allowed"] and email_check["allowed"]:
        print("Allowed to process chatbot message and send email")

    await reset_limit("demo-user-001", scope="user", limit_type="message")


if __name__ == "__main__":
    asyncio.run(main())
