import asyncio
import json
from typing import Any

from pydantic import BaseModel

from app.core.logger import log_error, log_event
from app.intelligence.structured_outputs.json_repair import recover_partial_json, repair_json, sanitize_json
from app.intelligence.structured_outputs.response_formatter import build_safe_response
from app.intelligence.structured_outputs.schema_validator import validate_response
from app.intelligence.structured_outputs.structured_models import ParsedOutput, StructuredResponse

MAX_OUTPUT_CHARS = 200_000


def extract_json(raw_response: object) -> str:
    text = sanitize_json(raw_response)
    if len(text) > MAX_OUTPUT_CHARS:
        raise ValueError("LLM output is too large to parse safely")

    extracted = recover_partial_json(text)
    if not extracted:
        raise ValueError("No JSON object or array found in LLM response")

    log_event("structured_output_json_extracted", extracted_length=len(extracted))
    return extracted


def detect_invalid_json(raw_json: str) -> bool:
    try:
        json.loads(raw_json)
        return False
    except json.JSONDecodeError as exc:
        log_event("structured_output_malformed_json_detected", error=str(exc), position=exc.pos)
        return True


def _parse_json(raw_json: str) -> Any:
    return json.loads(raw_json)


async def retry_parse(
    raw_response: object,
    *,
    schema_model: type[BaseModel] = StructuredResponse,
    max_retries: int = 2,
) -> ParsedOutput:
    attempts = 0
    current = str(raw_response or "")
    last_error = "Unable to parse AI response safely."

    while attempts <= max_retries:
        try:
            log_event("structured_output_retry_parse_attempt", attempt=attempts, max_retries=max_retries)
            extracted = extract_json(current)
            repaired = attempts > 0 or detect_invalid_json(extracted)
            if repaired:
                extracted = repair_json(extracted)

            payload = _parse_json(extracted)
            if isinstance(payload, list):
                if not payload:
                    raise ValueError("JSON array output is empty")
                payload = payload[0]
            validation = validate_response(payload, schema_model)
            if validation.success and validation.data is not None:
                return ParsedOutput(
                    success=True,
                    data=validation.data,
                    repaired=repaired,
                    retries_used=attempts,
                    raw_output=str(raw_response or ""),
                    normalized_output=extracted,
                    validation=validation,
                    metadata={"schema_model": schema_model.__name__},
                )
            last_error = validation.error or "Schema validation failed"
            current = repair_json(extracted)
        except Exception as exc:
            last_error = str(exc)
            log_error(
                "Structured output retry parse failed",
                attempt=attempts,
                max_retries=max_retries,
                error_type=type(exc).__name__,
            )
            current = repair_json(current)

        attempts += 1
        await asyncio.sleep(0)

    return build_safe_response(
        success=False,
        error=last_error,
        error_code="retry_overflow",
        raw_output=str(raw_response or ""),
        metadata={"schema_model": schema_model.__name__, "retries_used": max_retries},
    )


async def parse_output(
    raw_response: object,
    *,
    schema_model: type[BaseModel] = StructuredResponse,
    max_retries: int = 2,
) -> ParsedOutput:
    log_event("structured_output_parsing_started", schema_model=schema_model.__name__)
    try:
        parsed = await retry_parse(raw_response, schema_model=schema_model, max_retries=max_retries)
        if parsed.success:
            log_event(
                "structured_output_parsing_completed",
                schema_model=schema_model.__name__,
                repaired=parsed.repaired,
                retries_used=parsed.retries_used,
            )
            return build_safe_response(
                success=True,
                data=parsed.data,
                validation=parsed.validation,
                metadata=parsed.metadata | {"repaired": parsed.repaired, "retries_used": parsed.retries_used},
                apply_structured_defaults=issubclass(schema_model, StructuredResponse),
            ).model_copy(
                update={
                    "repaired": parsed.repaired,
                    "retries_used": parsed.retries_used,
                    "raw_output": parsed.raw_output,
                    "normalized_output": parsed.normalized_output,
                }
            )
        log_event("structured_output_parsing_failed", error_code=parsed.error_code, error=parsed.error)
        return parsed
    except Exception as exc:
        log_error("Structured output parsing crashed", error_type=type(exc).__name__, exc_info=True)
        return build_safe_response(success=False, error=str(exc), error_code="parsing_failed", raw_output=str(raw_response or ""))


async def parse_structured_response(
    raw_response: object,
    *,
    schema_model: type[BaseModel] = StructuredResponse,
    max_retries: int = 2,
) -> ParsedOutput:
    return await parse_output(raw_response, schema_model=schema_model, max_retries=max_retries)
