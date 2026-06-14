import asyncio
import inspect
import json
import logging
from dataclasses import dataclass
from typing import Any

from app.core.config import GROQ_TOOL_MODEL
from app.core.tool_router import TOOLS, execute_tool, list_tools
from app.intelligence.routing import route_request

logger = logging.getLogger(__name__)

DEFAULT_LLM_TIMEOUT_SECONDS = 20.0
DEFAULT_LLM_RETRIES = 2
DEFAULT_RETRY_BACKOFF_SECONDS = 0.5

SYSTEM_TOOL_PROMPT = """
You are an autonomous tool-selection layer for a FastAPI agentic AI chatbot backend.

Return exactly one JSON object and no extra text.

Valid response shape:
{
  "tool": "tool_name",
  "args": {}
}

If no backend tool should run, return:
{
  "tool": null,
  "args": {},
  "reason": "short reason"
}

Rules:
- Choose only from the provided tools.
- Use send_email for email sending.
- Use save_memory for short-term Redis memory.
- Use create_lead for CRM lead creation.
- Use book_meeting for calendar booking.
- Preserve user_id when available.
- Do not invent arguments that were not provided or reasonably inferred.
- Do not include markdown, code fences, comments, or prose outside JSON.
""".strip()

EXAMPLE_TOOL_PROMPTS: list[dict[str, str]] = [
    {
        "user": "Remember that user-123 wants a follow-up tomorrow.",
        "assistant": '{"tool":"save_memory","args":{"user_id":"user-123","message":{"role":"user","content":"wants a follow-up tomorrow"}}}',
    },
    {
        "user": "Create a CRM lead for Akshat at akshat@example.com.",
        "assistant": '{"tool":"create_lead","args":{"name":"Akshat","email":"akshat@example.com","lead_status":"NEW"}}',
    },
    {
        "user": "Book a demo tomorrow from 10:00 to 10:30 with lead@example.com.",
        "assistant": '{"tool":"book_meeting","args":{"user_id":"user-123","title":"Demo meeting","start_time":"2026-05-08T10:00:00+05:30","end_time":"2026-05-08T10:30:00+05:30","attendees":["lead@example.com"]}}',
    },
]


@dataclass(frozen=True)
class ToolCall:
    """Validated tool call emitted by the LLM."""

    tool: str | None
    args: dict[str, Any]
    reason: str | None = None


class AgentExecutorError(RuntimeError):
    """Raised when the agent executor cannot parse, validate, or execute an action."""


class ToolCallParseError(AgentExecutorError):
    """Raised when the LLM returns malformed JSON."""


class ToolCallValidationError(AgentExecutorError):
    """Raised when the parsed tool call is not executable."""


def _structured_response(
    *,
    success: bool,
    tool_call: dict[str, Any] | None = None,
    tool_result: dict[str, Any] | None = None,
    error: str | None = None,
    error_type: str | None = None,
    raw_model_output: str | None = None,
    attempts: int = 0,
) -> dict[str, Any]:
    return {
        "success": success,
        "tool_call": tool_call,
        "tool_result": tool_result,
        "error": error,
        "error_type": error_type,
        "raw_model_output": raw_model_output,
        "attempts": attempts,
    }


async def close_agent_executor_client() -> None:
    """Compatibility hook; model provider clients are owned by the routing layer."""


def _available_tools_for_prompt() -> str:
    tool_specs = []
    for tool in list_tools():
        tool_specs.append(
            {
                "name": tool["name"],
                "description": tool["description"],
                "args": tool["args"],
            }
        )

    return json.dumps(tool_specs, ensure_ascii=False)


def _build_messages(user_message: str, context: dict[str, Any] | None = None, correction: str | None = None) -> list[dict[str, str]]:
    context = context or {}
    user_payload = {
        "user_message": user_message,
        "context": context,
        "available_tools": json.loads(_available_tools_for_prompt()),
    }
    if correction:
        user_payload["previous_error"] = correction

    messages = [{"role": "system", "content": SYSTEM_TOOL_PROMPT}]
    for example in EXAMPLE_TOOL_PROMPTS:
        messages.append({"role": "user", "content": example["user"]})
        messages.append({"role": "assistant", "content": example["assistant"]})

    messages.append({"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)})
    return messages


async def _call_llm(user_message: str, context: dict[str, Any] | None = None, correction: str | None = None) -> str:
    response = await asyncio.wait_for(
        route_request(
            {
                "messages": _build_messages(user_message, context, correction),
                "task_type": "tool_calling",
                "preferred_model": GROQ_TOOL_MODEL,
                "temperature": 0,
                "max_tokens": 600,
                "metadata": {"entrypoint": "agent_executor"},
            }
        ),
        timeout=DEFAULT_LLM_TIMEOUT_SECONDS,
    )
    return response.content or ""


def _strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()

    return stripped


def _extract_json_object(text: str) -> dict[str, Any]:
    """Extract the first top-level JSON object to protect against model prose."""
    text = _strip_code_fence(text)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ToolCallParseError("LLM did not return a JSON object") from exc

        try:
            parsed = json.loads(text[start : end + 1])
        except json.JSONDecodeError as exc:
            raise ToolCallParseError(f"malformed tool JSON: {exc}") from exc

    if not isinstance(parsed, dict):
        raise ToolCallParseError("tool call must be a JSON object")

    return parsed


async def detect_tool_call(model_output: str) -> dict[str, Any]:
    """Parse raw LLM output into the required `{tool, args}` JSON shape."""
    payload = _extract_json_object(model_output)

    if "tool" not in payload:
        raise ToolCallValidationError("tool field is required")

    args = payload.get("args", {})
    if args is None:
        args = {}

    if not isinstance(args, dict):
        raise ToolCallValidationError("args must be a JSON object")

    tool = payload.get("tool")
    if tool is not None and not isinstance(tool, str):
        raise ToolCallValidationError("tool must be a string or null")

    return {"tool": tool, "args": args, "reason": payload.get("reason")}


async def validate_tool_args(tool_call: dict[str, Any]) -> dict[str, Any]:
    """Validate tool name and arguments before handing execution to the Tool Router."""
    tool_name = tool_call.get("tool")
    args = tool_call.get("args") or {}

    if tool_name is None:
        return {
            "valid": True,
            "tool_call": {"tool": None, "args": args, "reason": tool_call.get("reason")},
        }

    tool_definition = TOOLS.get(tool_name)
    if tool_definition is None:
        return {
            "valid": False,
            "error": f"Tool '{tool_name}' is not registered",
            "error_type": ToolCallValidationError.__name__,
        }

    try:
        inspect.signature(tool_definition.function).bind(**args)
    except TypeError as exc:
        return {
            "valid": False,
            "error": str(exc),
            "error_type": ToolCallValidationError.__name__,
        }

    return {"valid": True, "tool_call": {"tool": tool_name, "args": args}}


async def execute_agent_action(
    user_message: str,
    context: dict[str, Any] | None = None,
    retry_attempts: int = DEFAULT_LLM_RETRIES,
) -> dict[str, Any]:
    """
    Ask the LLM to select a tool, validate the JSON tool call, and execute it.

    Workflow: user message -> LLM JSON -> validation -> Tool Router -> structured result.
    """
    attempts = max(1, retry_attempts)
    raw_output = None
    correction = None
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            raw_output = await _call_llm(user_message, context, correction)
            tool_call = await detect_tool_call(raw_output)
            validation = await validate_tool_args(tool_call)
            if not validation["valid"]:
                raise ToolCallValidationError(validation["error"])

            validated_call = validation["tool_call"]
            if validated_call["tool"] is None:
                return _structured_response(
                    success=True,
                    tool_call=validated_call,
                    tool_result={
                        "success": True,
                        "tool": None,
                        "result": None,
                        "reason": tool_call.get("reason") or "No tool required",
                    },
                    raw_model_output=raw_output,
                    attempts=attempt,
                )

            tool_result = await execute_tool(validated_call["tool"], validated_call["args"])
            return _structured_response(
                success=bool(tool_result.get("success")),
                tool_call=validated_call,
                tool_result=tool_result,
                raw_model_output=raw_output,
                attempts=attempt,
            )
        except (TimeoutError, ToolCallParseError, ToolCallValidationError, AgentExecutorError) as exc:
            last_error = exc
            correction = f"Previous response failed: {exc}. Return only valid JSON with a registered tool and valid args."
            logger.warning("Agent action attempt failed: attempt=%s/%s error=%s", attempt, attempts, exc)
        except Exception as exc:
            last_error = exc
            correction = f"Previous tool selection failed: {exc}. Return only valid JSON."
            logger.exception("Unexpected agent executor failure: attempt=%s/%s", attempt, attempts)

        if attempt < attempts:
            await asyncio.sleep(DEFAULT_RETRY_BACKOFF_SECONDS * attempt)

    return _structured_response(
        success=False,
        error=str(last_error),
        error_type=type(last_error).__name__ if last_error else AgentExecutorError.__name__,
        raw_model_output=raw_output,
        attempts=attempts,
    )
