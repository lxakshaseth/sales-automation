from typing import Any

from app.agents import tool_router as _agent_tool_router  # noqa: F401 - registers agent tools
from app.agents.workflow_engine import run_workflow
from app.core.agent_executor import execute_agent_action
from app.core.logger import log_error, log_event
from app.services.groq_service import GroqServiceError, generate_sales_reply
from app.services.memory_service import get_recent_history

PROMPT_INJECTION_MARKERS = (
    "ignore previous instructions",
    "developer message",
    "system prompt",
    "reveal your prompt",
    "act as chatgpt",
)


def detect_prompt_injection(message: str) -> bool:
    normalized = str(message or "").lower()
    return any(marker in normalized for marker in PROMPT_INJECTION_MARKERS)


async def run_agent(
    *,
    user_id: str,
    message: str,
    preferred_language: str = "en",
    media_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Agentic orchestration: guardrails -> workflow hints -> tool selection -> final reply.
    """
    if detect_prompt_injection(message):
        log_event("abuse_detected", user_id=user_id, reason="prompt_injection_marker")
        return {
            "reply": "I can help with product details, meetings, demos, and follow-ups. What would you like to do next?",
            "tool_result": None,
            "workflow": {"blocked": True, "reason": "prompt_injection"},
        }

    history = await get_recent_history(user_id)
    workflow = await run_workflow(user_id, message, {"history": history, "media_context": media_context})
    tool_result = None

    if not workflow.get("handled"):
        agent_context = {
            "user_id": user_id,
            "preferred_language": preferred_language,
            "workflow": workflow,
            "media_context": media_context,
            "recent_history": history[-6:],
        }
        tool_result = await execute_agent_action(message, agent_context)
        selected_tool = (tool_result.get("tool_call") or {}).get("tool")
        if selected_tool:
            log_event("tool_selected", user_id=user_id, tool=selected_tool, success=tool_result.get("success"))
    else:
        tool_result = workflow.get("tool_result")

    final_context = {
        "workflow": workflow,
        "tool_result": tool_result,
        "recent_history": history[-6:],
    }
    try:
        reply = await generate_sales_reply(
            f"{message}\n\nAgent context: {final_context}",
            user_id=user_id,
            media_context=media_context,
            preferred_language=preferred_language,
        )
    except GroqServiceError as exc:
        log_error("Agent final response failed", user_id=user_id, error=str(exc))
        reply = "Sorry, I am having trouble responding right now. Please try again shortly."

    return {"reply": reply, "tool_result": tool_result, "workflow": workflow}
