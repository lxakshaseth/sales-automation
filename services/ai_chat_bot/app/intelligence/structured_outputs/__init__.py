"""Structured Output Engine for machine-safe AI responses."""

from app.intelligence.structured_outputs.json_repair import (
    fix_brackets,
    fix_quotes,
    recover_partial_json,
    repair_json,
    sanitize_json,
)
from app.intelligence.structured_outputs.output_parser import (
    detect_invalid_json,
    extract_json,
    parse_output,
    parse_structured_response,
    retry_parse,
)
from app.intelligence.structured_outputs.response_formatter import (
    apply_defaults,
    build_safe_response,
    format_response,
    normalize_fields,
)
from app.intelligence.structured_outputs.schema_validator import (
    validate_confidence_score,
    validate_response,
    validate_schema,
    validate_tool_output,
)
from app.intelligence.structured_outputs.structured_models import (
    STRUCTURED_OUTPUT_VERSION,
    ConfidenceResponse,
    ErrorResponse,
    ParsedOutput,
    StructuredResponse,
    StructuredToolOutput,
    ToolIntentResponse,
    ValidationResult,
)

__all__ = [
    "STRUCTURED_OUTPUT_VERSION",
    "ConfidenceResponse",
    "ErrorResponse",
    "ParsedOutput",
    "StructuredResponse",
    "StructuredToolOutput",
    "ToolIntentResponse",
    "ValidationResult",
    "apply_defaults",
    "build_safe_response",
    "detect_invalid_json",
    "extract_json",
    "fix_brackets",
    "fix_quotes",
    "format_response",
    "normalize_fields",
    "parse_output",
    "parse_structured_response",
    "recover_partial_json",
    "repair_json",
    "retry_parse",
    "sanitize_json",
    "validate_confidence_score",
    "validate_response",
    "validate_schema",
    "validate_tool_output",
]

