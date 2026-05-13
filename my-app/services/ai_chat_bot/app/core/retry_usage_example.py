import asyncio

from app.core.retry_handler import retry_async, retry_sync


@retry_async(max_attempts=3, base_delay_seconds=1, timeout_seconds=10)
async def send_whatsapp_message(to: str, body: str) -> dict:
    # Replace with the real WhatsApp provider call.
    return {"to": to, "body": body, "sent": True}


@retry_sync(max_attempts=3, base_delay_seconds=1, timeout_seconds=10)
def call_legacy_email_sdk(to: str, subject: str) -> dict:
    # Use this for synchronous SDKs that do not provide async clients.
    return {"to": to, "subject": subject, "queued": True}


async def main() -> None:
    print(await send_whatsapp_message("+10000000000", "Your meeting starts soon."))
    print(call_legacy_email_sdk("lead@example.com", "Meeting confirmed"))


if __name__ == "__main__":
    asyncio.run(main())
