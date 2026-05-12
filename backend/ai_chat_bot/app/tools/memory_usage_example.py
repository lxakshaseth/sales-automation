import asyncio

from app.tools.memory_tool import append_memory, clear_memory, get_memory, save_memory


async def main() -> None:
    user_id = "demo-user-001"

    # Start a new conversation memory window for this user.
    await save_memory(
        user_id,
        {"role": "system", "content": "Remember this user's sales follow-up context."},
    )

    # Store each turn as a JSON-serializable message object.
    await append_memory(user_id, {"role": "user", "content": "Follow up with Acme tomorrow."})
    await append_memory(
        user_id,
        {"role": "assistant", "content": "Noted. I will keep that in short-term context."},
    )

    history = await get_memory(user_id)
    print(history)

    # Use this when the user starts over, logs out, or requests memory deletion.
    await clear_memory(user_id)


if __name__ == "__main__":
    asyncio.run(main())
