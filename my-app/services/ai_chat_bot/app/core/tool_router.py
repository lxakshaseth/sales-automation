import asyncio
import inspect
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from app.tools.calendar_tool import (
    book_meeting,
    cancel_meeting,
    check_availability,
    create_event,
    get_upcoming_events,
    reschedule_meeting,
)
from app.tools.crm_tool import add_note, create_lead, get_contact, update_customer, update_lead_status
from app.tools.email_tool import send_email
from app.tools.memory_tool import get_memory, save_memory
from app.tools.mongo_tool import save_chat

logger = logging.getLogger(__name__)

ToolFunction = Callable[..., Awaitable[Any]]

DEFAULT_TOOL_TIMEOUT_SECONDS = 15.0
DEFAULT_TOOL_RETRIES = 1
DEFAULT_RETRY_BACKOFF_SECONDS = 0.25


@dataclass(frozen=True)
class ToolDefinition:
    """Metadata for a callable tool exposed to the agent runtime."""

    name: str
    function: ToolFunction
    description: str
    timeout_seconds: float = DEFAULT_TOOL_TIMEOUT_SECONDS
    retries: int = DEFAULT_TOOL_RETRIES


class ToolRouterError(RuntimeError):
    """Base error for tool router failures."""


class ToolNotFoundError(ToolRouterError):
    """Raised when the model asks for a tool that is not registered."""


class ToolValidationError(ToolRouterError):
    """Raised when tool arguments do not match the registered function signature."""


class ToolExecutionError(ToolRouterError):
    """Raised when a registered tool fails after all retry attempts."""


TOOLS: dict[str, ToolDefinition] = {}


def _structured_response(
    *,
    success: bool,
    tool_name: str,
    result: Any = None,
    error: str | None = None,
    error_type: str | None = None,
    attempts: int = 0,
) -> dict[str, Any]:
    """Return a stable JSON-serializable envelope for agent orchestration."""
    return {
        "success": success,
        "tool": tool_name,
        "result": result,
        "error": error,
        "error_type": error_type,
        "attempts": attempts,
    }


def _validate_tool_function(function: ToolFunction) -> None:
    if not callable(function):
        raise TypeError("tool function must be callable")

    if not inspect.iscoroutinefunction(function):
        raise TypeError("tool function must be async")


def _validate_tool_args(tool: ToolDefinition, args: dict[str, Any]) -> None:
    if not isinstance(args, dict):
        raise ToolValidationError("tool args must be a JSON object")

    try:
        inspect.signature(tool.function).bind(**args)
    except TypeError as exc:
        raise ToolValidationError(str(exc)) from exc


def register_tool(
    name: str,
    function: ToolFunction,
    description: str = "",
    timeout_seconds: float = DEFAULT_TOOL_TIMEOUT_SECONDS,
    retries: int = DEFAULT_TOOL_RETRIES,
) -> ToolDefinition:
    """
    Register a tool that the AI model may request.

    Future channels such as WhatsApp can be added by calling this once during app
    startup, without changing the router execution path.
    """
    if not name or not name.strip():
        raise ValueError("tool name is required")

    _validate_tool_function(function)

    tool = ToolDefinition(
        name=name.strip(),
        function=function,
        description=description,
        timeout_seconds=max(0.1, float(timeout_seconds)),
        retries=max(0, int(retries)),
    )
    TOOLS[tool.name] = tool
    logger.info("Registered tool: %s", tool.name)
    return tool


def list_tools() -> list[dict[str, Any]]:
    """List tool metadata for prompts, observability, and multi-agent planning."""
    tools = []
    for tool in TOOLS.values():
        signature = inspect.signature(tool.function)
        tools.append(
            {
                "name": tool.name,
                "description": tool.description,
                "args": list(signature.parameters.keys()),
                "timeout_seconds": tool.timeout_seconds,
                "retries": tool.retries,
            }
        )

    return sorted(tools, key=lambda item: item["name"])


async def _call_tool_with_timeout(tool: ToolDefinition, args: dict[str, Any]) -> Any:
    return await asyncio.wait_for(tool.function(**args), timeout=tool.timeout_seconds)


async def execute_tool(tool_name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Validate and execute one model-selected tool.

    Expected model output:
    {"tool": "send_email", "args": {"to": "user@gmail.com", "subject": "Meeting", "body": "Hello"}}
    """
    args = args or {}
    tool = TOOLS.get(tool_name)

    if tool is None:
        logger.warning("Tool not found: %s", tool_name)
        return _structured_response(
            success=False,
            tool_name=tool_name,
            error=f"Tool '{tool_name}' is not registered",
            error_type=ToolNotFoundError.__name__,
        )

    try:
        _validate_tool_args(tool, args)
    except ToolValidationError as exc:
        logger.warning("Invalid args for tool=%s: %s", tool_name, exc)
        return _structured_response(
            success=False,
            tool_name=tool_name,
            error=str(exc),
            error_type=ToolValidationError.__name__,
        )

    max_attempts = tool.retries + 1
    for attempt in range(1, max_attempts + 1):
        try:
            result = await _call_tool_with_timeout(tool, args)
            logger.info("Tool executed successfully: %s", tool_name)
            return _structured_response(
                success=True,
                tool_name=tool_name,
                result=result,
                attempts=attempt,
            )
        except TimeoutError:
            error: Exception = ToolExecutionError(f"Tool '{tool_name}' timed out")
            logger.warning("Tool timeout on attempt %s/%s: %s", attempt, max_attempts, tool_name)
        except Exception as exc:
            error = exc
            logger.exception("Tool failed on attempt %s/%s: %s", attempt, max_attempts, tool_name)

        if attempt < max_attempts:
            await asyncio.sleep(DEFAULT_RETRY_BACKOFF_SECONDS * attempt)

    return _structured_response(
        success=False,
        tool_name=tool_name,
        error=str(error),
        error_type=type(error).__name__,
        attempts=max_attempts,
    )


def register_default_tools() -> None:
    """Register built-in tools for the current agent backend."""
    register_tool(
        "send_email",
        send_email,
        description="Send an email to a user or lead.",
        timeout_seconds=20,
        retries=1,
    )
    register_tool(
        "save_memory",
        save_memory,
        description="Save short-term Redis conversation memory for a user.",
        timeout_seconds=5,
        retries=1,
    )
    register_tool(
        "get_memory",
        get_memory,
        description="Read short-term Redis conversation memory for a user.",
        timeout_seconds=5,
        retries=1,
    )
    register_tool(
        "save_chat",
        save_chat,
        description="Persist conversation logs, intents, summaries, and lead status in MongoDB.",
        timeout_seconds=10,
        retries=1,
    )
    register_tool(
        "create_lead",
        create_lead,
        description="Create a HubSpot CRM contact for an AI-detected lead.",
        timeout_seconds=15,
        retries=1,
    )
    register_tool(
        "update_customer",
        update_customer,
        description="Update a HubSpot CRM contact by email or contact ID.",
        timeout_seconds=15,
        retries=1,
    )
    register_tool(
        "add_note",
        add_note,
        description="Add an AI-generated timeline note to a HubSpot contact.",
        timeout_seconds=15,
        retries=1,
    )
    register_tool(
        "get_contact",
        get_contact,
        description="Fetch a HubSpot CRM contact by email or contact ID.",
        timeout_seconds=10,
        retries=1,
    )
    register_tool(
        "update_lead_status",
        update_lead_status,
        description="Update a HubSpot contact lead status and optional AI summary.",
        timeout_seconds=15,
        retries=1,
    )
    register_tool(
        "create_event",
        create_event,
        description="Create a Google Calendar event with optional Google Meet link.",
        timeout_seconds=15,
        retries=1,
    )
    register_tool(
        "book_meeting",
        book_meeting,
        description="Book a meeting, send confirmation, and schedule a reminder.",
        timeout_seconds=25,
        retries=1,
    )
    register_tool(
        "cancel_meeting",
        cancel_meeting,
        description="Cancel a Google Calendar meeting.",
        timeout_seconds=10,
        retries=1,
    )
    register_tool(
        "reschedule_meeting",
        reschedule_meeting,
        description="Reschedule a Google Calendar meeting and refresh reminder metadata.",
        timeout_seconds=15,
        retries=1,
    )
    register_tool(
        "get_upcoming_events",
        get_upcoming_events,
        description="Fetch upcoming Google Calendar events for planning.",
        timeout_seconds=10,
        retries=1,
    )
    register_tool(
        "check_availability",
        check_availability,
        description="Find free Google Calendar slots for meeting booking.",
        timeout_seconds=10,
        retries=1,
    )


register_default_tools()
