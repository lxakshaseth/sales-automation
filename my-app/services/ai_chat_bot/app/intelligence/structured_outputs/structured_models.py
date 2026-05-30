from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictFloat, StrictStr, field_validator

STRUCTURED_OUTPUT_VERSION = "v1"

ErrorCode = Literal[
    "malformed_json",
    "invalid_schema",
    "invalid_confidence",
    "parsing_failed",
    "retry_overflow",
    "unsupported_format",
]


class StrictBaseModel(BaseModel):
    """Forbid extra AI-generated fields by default for automation safety."""

    model_config = ConfigDict(extra="forbid", strict=True)


class StructuredResponse(StrictBaseModel):
    intent: StrictStr
    confidence: StrictFloat = Field(ge=0.0, le=1.0)
    tool_required: StrictBool = False
    tool_name: StrictStr | None = None
    entities: dict[str, Any] = Field(default_factory=dict)

    @field_validator("intent")
    @classmethod
    def validate_intent(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("intent cannot be empty")
        return normalized

    @field_validator("tool_name")
    @classmethod
    def validate_tool_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        if not normalized:
            raise ValueError("tool_name cannot be empty")
        return normalized


class ToolIntentResponse(StructuredResponse):
    tool_required: StrictBool
    tool_name: StrictStr | None = None

    @field_validator("tool_name")
    @classmethod
    def validate_required_tool_name(cls, value: str | None, info) -> str | None:
        if info.data.get("tool_required") is True and not value:
            raise ValueError("tool_name is required when tool_required is true")
        return value


class ConfidenceResponse(StrictBaseModel):
    confidence: StrictFloat = Field(ge=0.0, le=1.0)
    reason: StrictStr | None = None


class StructuredToolOutput(StrictBaseModel):
    success: StrictBool
    tool_name: StrictStr
    intent: StrictStr | None = None
    confidence: StrictFloat = Field(default=0.0, ge=0.0, le=1.0)
    result: dict[str, Any] = Field(default_factory=dict)
    error: StrictStr | None = None

    @field_validator("tool_name")
    @classmethod
    def validate_tool_name(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("tool_name cannot be empty")
        return normalized


class ErrorResponse(StrictBaseModel):
    success: StrictBool = False
    error: StrictStr
    error_code: ErrorCode = "parsing_failed"
    raw_output: StrictStr | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ValidationResult(StrictBaseModel):
    success: StrictBool
    data: dict[str, Any] | None = None
    error: StrictStr | None = None
    error_code: ErrorCode | None = None
    model_name: StrictStr | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ParsedOutput(StrictBaseModel):
    success: StrictBool
    data: dict[str, Any] | None = None
    repaired: StrictBool = False
    retries_used: int = Field(default=0, ge=0)
    error: StrictStr | None = None
    error_code: ErrorCode | None = None
    raw_output: StrictStr | None = None
    normalized_output: StrictStr | None = None
    validation: ValidationResult | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

