import asyncio

from app.core.event_bus import EVENT_MESSAGE_RECEIVED, emit_event, subscribe_event
from app.tools.memory_tool import append_memory


async def save_message_memory(event: dict) -> dict:
    payload = event["payload"]
    history = await append_memory(
        payload["user_id"],
        {"role": "user", "content": payload["message"], "timestamp": event["timestamp"]},
    )
    return {"memory_count": len(history)}


subscribe_event(EVENT_MESSAGE_RECEIVED, save_message_memory)


async def main() -> None:
    result = await emit_event(
        EVENT_MESSAGE_RECEIVED,
        payload={"user_id": "demo-user-001", "message": "I want to book a demo tomorrow."},
        metadata={"source": "chatbot"},
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
