from typing import Any

from app.core.logger import log_event
from app.intelligence.structured_outputs.structured_models import ErrorResponse, ParsedOutput, ValidationResult

DEFAULT_STRUCTURED_RESPONSE: dict[str, Any] = {
    "intent": "unknown",
    "confidence": 0.0,
    "tool_required": False,
    "tool_name": None,
    "entities": {},
}


def normalize_fields(data: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in data.items():
        clean_key = str(key).strip()
        if not clean_key:
            continue
        if isinstance(value, str):
            normalized[clean_key] = value.strip()
        elif isinstance(value, dict):
            normalized[clean_key] = normalize_fields(value)
        elif isinstance(value, list):
            normalized[clean_key] = [item.strip() if isinstance(item, str) else item for item in value]
        else:
            normalized[clean_key] = value
    return normalized


def apply_defaults(data: dict[str, Any], defaults: dict[str, Any] | None = None) -> dict[str, Any]:
    base = dict(defaults or DEFAULT_STRUCTURED_RESPONSE)
    base.update({key: value for key, value in data.items() if value is not None})
    if not isinstance(base.get("entities"), dict):
        base["entities"] = {}
    if base.get("tool_required") is False:
        base["tool_name"] = None
    return base


def format_response(data: dict[str, Any], defaults: dict[str, Any] | None = None) -> dict[str, Any]:
    formatted = apply_defaults(normalize_fields(data), defaults)
    log_event("structured_output_formatting_completed", keys=list(formatted.keys()))
    return formatted


def build_safe_response(
    *,
    success: bool,
    data: dict[str, Any] | None = None,
    error: str | None = None,
    error_code: str = "parsing_failed",
    raw_output: str | None = None,
    validation: ValidationResult | None = None,
    metadata: dict[str, Any] | None = None,
    apply_structured_defaults: bool = True,
) -> ParsedOutput:
    if success and data is not None:
        safe_data = format_response(data) if apply_structured_defaults else normalize_fields(data)
        return ParsedOutput(success=True, data=safe_data, validation=validation, metadata=metadata or {})

    fallback = ErrorResponse(
        success=False,
        error=error or "Unable to parse AI response safely.",
        error_code=error_code,
        raw_output=raw_output,
        details=metadata or {},
    )
    log_event("structured_output_fallback_response", error_code=error_code)
    return ParsedOutput(
        success=False,
        data=fallback.model_dump(mode="json", exclude_none=True),
        error=fallback.error,
        error_code=fallback.error_code,
        raw_output=raw_output,
        validation=validation,
        metadata=metadata or {},
    )
