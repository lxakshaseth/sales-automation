import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core import agent_executor
from app.core.agent_executor import (
    ToolCallParseError,
    ToolCallValidationError,
    detect_tool_call,
    execute_agent_action,
    validate_tool_args,
)


class AgentExecutorTests(unittest.IsolatedAsyncioTestCase):
    async def test_detect_tool_call_parses_plain_json(self):
        result = await detect_tool_call('{"tool":"send_email","args":{"to":"a@test.com","subject":"Hi","body":"Hello"}}')

        self.assertEqual(result["tool"], "send_email")
        self.assertEqual(result["args"]["to"], "a@test.com")

    async def test_detect_tool_call_parses_fenced_json(self):
        result = await detect_tool_call('```json\n{"tool":null,"args":{},"reason":"chat only"}\n```')

        self.assertIsNone(result["tool"])
        self.assertEqual(result["reason"], "chat only")

    async def test_detect_tool_call_rejects_malformed_json(self):
        with self.assertRaises(ToolCallParseError):
            await detect_tool_call("not json")

    async def test_detect_tool_call_rejects_missing_tool(self):
        with self.assertRaises(ToolCallValidationError):
            await detect_tool_call('{"args":{}}')

    async def test_validate_tool_args_accepts_registered_tool(self):
        result = await validate_tool_args(
            {"tool": "send_email", "args": {"to": "a@test.com", "subject": "Hi", "body": "Hello"}}
        )

        self.assertTrue(result["valid"])

    async def test_validate_tool_args_rejects_missing_tool(self):
        result = await validate_tool_args({"tool": "missing_tool", "args": {}})

        self.assertFalse(result["valid"])
        self.assertEqual(result["error_type"], "ToolCallValidationError")

    async def test_validate_tool_args_rejects_bad_args(self):
        result = await validate_tool_args({"tool": "send_email", "args": {"to": "a@test.com"}})

        self.assertFalse(result["valid"])

    async def test_execute_agent_action_executes_tool_router(self):
        with (
            patch.object(
                agent_executor,
                "_call_llm",
                new=AsyncMock(return_value='{"tool":"save_memory","args":{"user_id":"user-123","message":"hello"}}'),
            ),
            patch.object(agent_executor, "execute_tool", new=AsyncMock(return_value={"success": True, "tool": "save_memory"})) as mock_execute,
        ):
            result = await execute_agent_action("remember hello", retry_attempts=1)

        self.assertTrue(result["success"])
        self.assertEqual(result["tool_call"]["tool"], "save_memory")
        mock_execute.assert_awaited_once_with("save_memory", {"user_id": "user-123", "message": "hello"})

    async def test_execute_agent_action_handles_no_tool(self):
        with patch.object(
            agent_executor,
            "_call_llm",
            new=AsyncMock(return_value='{"tool":null,"args":{},"reason":"No backend action needed"}'),
        ):
            result = await execute_agent_action("hello", retry_attempts=1)

        self.assertTrue(result["success"])
        self.assertIsNone(result["tool_call"]["tool"])
        self.assertEqual(result["tool_result"]["reason"], "No backend action needed")

    async def test_execute_agent_action_retries_malformed_json(self):
        llm = AsyncMock(
            side_effect=[
                "not-json",
                '{"tool":"send_email","args":{"to":"a@test.com","subject":"Hi","body":"Hello"}}',
            ]
        )

        with (
            patch.object(agent_executor, "_call_llm", new=llm),
            patch.object(agent_executor.asyncio, "sleep", new=AsyncMock()),
            patch.object(agent_executor.logger, "warning"),
            patch.object(agent_executor, "execute_tool", new=AsyncMock(return_value={"success": True})),
        ):
            result = await execute_agent_action("send an email", retry_attempts=2)

        self.assertTrue(result["success"])
        self.assertEqual(result["attempts"], 2)

    async def test_execute_agent_action_returns_failure_after_retries(self):
        with (
            patch.object(agent_executor, "_call_llm", new=AsyncMock(return_value="not-json")),
            patch.object(agent_executor.asyncio, "sleep", new=AsyncMock()),
            patch.object(agent_executor.logger, "warning"),
        ):
            result = await execute_agent_action("bad", retry_attempts=2)

        self.assertFalse(result["success"])
        self.assertEqual(result["error_type"], "ToolCallParseError")

    async def test_close_agent_executor_client(self):
        client = MagicMock()
        client.close = AsyncMock()
        agent_executor._groq_client = client

        await agent_executor.close_agent_executor_client()

        client.close.assert_awaited_once()
        self.assertIsNone(agent_executor._groq_client)


if __name__ == "__main__":
    unittest.main()
