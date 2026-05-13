import asyncio
import unittest
from unittest.mock import patch

from app.core import tool_router
from app.core.tool_router import (
    ToolValidationError,
    execute_tool,
    list_tools,
    register_tool,
)


async def successful_tool(user_id: str, message: str) -> dict:
    return {"user_id": user_id, "message": message}


async def flaky_tool() -> str:
    flaky_tool.calls += 1
    if flaky_tool.calls == 1:
        raise RuntimeError("temporary failure")
    return "ok"


flaky_tool.calls = 0


async def slow_tool() -> str:
    await asyncio.sleep(0.2)
    return "too late"


def sync_tool() -> None:
    return None


class ToolRouterTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.original_tools = tool_router.TOOLS.copy()
        tool_router.TOOLS.clear()

    def tearDown(self):
        tool_router.TOOLS.clear()
        tool_router.TOOLS.update(self.original_tools)
        flaky_tool.calls = 0

    async def test_register_and_list_tools(self):
        register_tool("successful_tool", successful_tool, "Test tool")

        tools = list_tools()

        self.assertEqual(tools[0]["name"], "successful_tool")
        self.assertEqual(tools[0]["args"], ["user_id", "message"])

    async def test_execute_tool_returns_structured_success(self):
        register_tool("successful_tool", successful_tool)

        result = await execute_tool(
            "successful_tool",
            {"user_id": "user-123", "message": "Hello"},
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["result"], {"user_id": "user-123", "message": "Hello"})
        self.assertEqual(result["attempts"], 1)

    async def test_execute_tool_validates_missing_tools(self):
        with patch.object(tool_router.logger, "warning"):
            result = await execute_tool("missing_tool", {})

        self.assertFalse(result["success"])
        self.assertEqual(result["error_type"], "ToolNotFoundError")

    async def test_execute_tool_validates_args(self):
        register_tool("successful_tool", successful_tool)

        with patch.object(tool_router.logger, "warning"):
            result = await execute_tool("successful_tool", {"user_id": "user-123"})

        self.assertFalse(result["success"])
        self.assertEqual(result["error_type"], ToolValidationError.__name__)

    async def test_execute_tool_retries_failed_tools(self):
        register_tool("flaky_tool", flaky_tool, retries=1)

        with patch.object(tool_router.logger, "exception"):
            result = await execute_tool("flaky_tool", {})

        self.assertTrue(result["success"])
        self.assertEqual(result["result"], "ok")
        self.assertEqual(result["attempts"], 2)

    async def test_execute_tool_times_out(self):
        register_tool("slow_tool", slow_tool, timeout_seconds=0.01, retries=0)

        with patch.object(tool_router.logger, "warning"):
            result = await execute_tool("slow_tool", {})

        self.assertFalse(result["success"])
        self.assertEqual(result["error_type"], "ToolExecutionError")

    async def test_register_tool_requires_async_function(self):
        with self.assertRaises(TypeError):
            register_tool("sync_tool", sync_tool)


if __name__ == "__main__":
    unittest.main()
