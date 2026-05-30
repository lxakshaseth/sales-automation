import json
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.intelligence.prompts.system_prompts import PROMPT_VERSION, PromptTemplate


class ToolSpec(BaseModel):
    name: str
    description: str
    args_schema: dict[str, Any] = Field(default_factory=dict)
    risk_level: str = "standard"

    @field_validator("name", "description")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("tool fields cannot be empty")
        return normalized


class ToolResultContext(BaseModel):
    tool_name: str
    success: bool
    result: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


TOOL_SELECTION_PROMPT = PromptTemplate(
    name="tool_selection",
    version=PROMPT_VERSION,
    description="Select tools and produce strict JSON arguments safely.",
    template="""
Tool calling rules:
- Return tool arguments only when supported by the user's request and context.
- Use strict JSON for tool decisions and arguments.
- Do not infer required fields that are absent; use null only if the tool schema allows it.
- Never claim an email, WhatsApp message, CRM update, or calendar booking succeeded unless the executed tool result has success=true.
- If no tool should run, return tool_required=false with a short reason.
""".strip(),
    tags=["tools", "json", "safe-execution"],
)

TOOL_FAILURE_FALLBACK = """
Tool execution did not confirm success. Explain that the action could not be completed or verified, and provide the tool error if available.
Do not say "sent", "booked", "updated", or "completed" unless the tool result confirms success.
""".strip()


def render_tool_context(tools: list[ToolSpec], tool_outputs: list[ToolResultContext]) -> str:
    tool_payload = [
        {
            "name": tool.name,
            "description": tool.description,
            "args_schema": tool.args_schema,
            "risk_level": tool.risk_level,
        }
        for tool in tools
    ]
    result_payload = [
        {
            "tool_name": output.tool_name,
            "success": output.success,
            "result": output.result,
            "error": output.error,
        }
        for output in tool_outputs
    ]
    return "\n".join(
        [
            "Available tools JSON:",
            json.dumps(tool_payload, ensure_ascii=False, default=str),
            "Executed tool results JSON:",
            json.dumps(result_payload, ensure_ascii=False, default=str),
        ]
    )

