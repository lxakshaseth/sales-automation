import asyncio
from app.tools.email_tool import send_email

async def main():

    result = await send_email(
        "lxakshatseth90@gmail.com",
        "AI Agent Test",
        "<h1>Hello from AI Agent</h1>"
    )

    print(result)

asyncio.run(main())