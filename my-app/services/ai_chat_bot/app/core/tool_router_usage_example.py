import asyncio

from app.core.tool_router import execute_tool, list_tools


async def main() -> None:
    print(list_tools())

    ai_response = {
        "tool": "save_memory",
        "args": {
            "user_id": "demo-user-001",
            "message": {"role": "user", "content": "Follow up tomorrow."},
        },
    }

    result = await execute_tool(ai_response["tool"], ai_response["args"])
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
