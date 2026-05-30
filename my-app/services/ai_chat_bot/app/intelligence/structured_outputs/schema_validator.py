from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from app.core.logger import log_error, log_event
from app.intelligence.structured_outputs.structured_models import (
    ConfidenceResponse,
    StructuredResponse,
    StructuredToolOutput,
    ToolIntentResponse,
    ValidationResult,
)

SchemaModel = TypeVar("SchemaModel", bound=BaseModel)


def validate_confidence_score(value: object) -> float:
    if not isinstance(value, float):
        raise ValueError("confidence must be a float")
    if value < 0.0 or value > 1.0:
        raise ValueError("confidence must be between 0.0 and 1.0")
    return value


def validate_schema(data: dict[str, Any], schema_model: type[SchemaModel] = StructuredResponse) -> SchemaModel:
    validated = schema_model.model_validate(data)
    log_event("structured_output_schema_validated", schema_model=schema_model.__name__)
    return validated


def validate_response(data: object, schema_model: type[SchemaModel] = StructuredResponse) -> ValidationResult:
    if not isinstance(data, dict):
        log_event("structured_output_validation_failed", reason="not_dict", schema_model=schema_model.__name__)
        return ValidationResult(success=False, error="Structured output must be a JSON object.", error_code="invalid_schema")

    try:
        if "confidence" in data:
            validate_confidence_score(data["confidence"])
        validated = validate_schema(data, schema_model)
        return ValidationResult(
            success=True,
            data=validated.model_dump(mode="json", exclude_none=True),
            model_name=schema_model.__name__,
        )
    except (ValidationError, ValueError) as exc:
        log_error(
            "Structured output validation failed",
            error_type=type(exc).__name__,
            schema_model=schema_model.__name__,
            exc_info=True,
        )
        return ValidationResult(
            success=False,
            error=str(exc),
            error_code="invalid_confidence" if "confidence" in str(exc).lower() else "invalid_schema",
            model_name=schema_model.__name__,
        )


def validate_tool_output(data: object) -> ValidationResult:
    return validate_response(data, StructuredToolOutput)


def validate_tool_intent(data: object) -> ValidationResult:
    return validate_response(data, ToolIntentResponse)


def validate_confidence_response(data: object) -> ValidationResult:
    return validate_response(data, ConfidenceResponse)

