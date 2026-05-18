from typing import Literal

from pydantic import BaseModel, Field, field_validator


PromptMode = Literal["conversational", "rag_qa", "memory_aware", "enterprise_assistant", "tool_calling"]


class PromptTemplate(BaseModel):
    name: str
    mode: PromptMode = "enterprise_assistant"
    system_template: str
    user_template: str
    guardrails: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

    @field_validator("name", "system_template", "user_template")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("prompt template fields cannot be empty")
        return normalized


class PromptBuildRequest(BaseModel):
    user_query: str
    template_name: str = "enterprise_assistant"
    language_hint: str | None = None
    role: str = "enterprise_ai_assistant"
    metadata: dict = Field(default_factory=dict)


class PromptBuildResult(BaseModel):
    final_prompt: str
    messages: list[dict[str, str]] = Field(default_factory=list)
    template_name: str
    token_count: int = Field(default=0, ge=0)
    metadata: dict = Field(default_factory=dict)

