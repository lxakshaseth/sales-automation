import asyncio
import json

from app.intelligence.structured_outputs import (
    StructuredResponse,
    StructuredToolOutput,
    detect_invalid_json,
    parse_output,
    repair_json,
    validate_response,
    validate_tool_output,
)


def test_repair_json_adds_missing_commas_and_preserves_unicode() -> None:
    raw = """
    {
      "intent": "send_email"
      "confidence": 0.94
      "tool_required": true,
      "tool_name": "send_email",
      "entities": {"subject": "मीटिंग Reminder",}
    }
    """

    repaired = repair_json(raw)
    payload = json.loads(repaired)

    assert payload["intent"] == "send_email"
    assert payload["confidence"] == 0.94
    assert payload["entities"]["subject"] == "मीटिंग Reminder"
    assert detect_invalid_json(repaired) is False


def test_schema_validation_rejects_extra_fields_and_non_float_confidence() -> None:
    invalid = {
        "intent": "send_email",
        "confidence": 1,
        "tool_required": True,
        "tool_name": "send_email",
        "entities": {},
        "hallucinated_success": "Email sent successfully",
    }

    result = validate_response(invalid, StructuredResponse)

    assert result.success is False
    assert result.error_code in {"invalid_schema", "invalid_confidence"}


def test_tool_output_validation_requires_confirmed_success_shape() -> None:
    valid = {
        "success": True,
        "tool_name": "send_email",
        "intent": "send_email",
        "confidence": 0.88,
        "result": {"message_id": "msg-123"},
        "error": None,
    }

    result = validate_tool_output(valid)

    assert result.success is True
    assert result.data["success"] is True
    assert result.data["tool_name"] == "send_email"


def test_parse_output_repairs_and_formats_machine_safe_response() -> None:
    raw = """
    Sure, here is the JSON:
    {
      "intent": "send_email"
      "confidence": 0.94
      "tool_required": true
      "tool_name": "send_email"
      "entities": {"email": "test@example.com", "subject": "Meeting Reminder"}
    }
    """

    result = asyncio.run(parse_output(raw, schema_model=StructuredResponse, max_retries=2))

    assert result.success is True
    assert result.repaired is True
    assert result.data["intent"] == "send_email"
    assert result.data["tool_required"] is True
    assert result.data["entities"]["email"] == "test@example.com"


def test_parse_output_returns_safe_fallback_after_retry_overflow() -> None:
    result = asyncio.run(parse_output("not json at all", max_retries=1))

    assert result.success is False
    assert result.data["success"] is False
    assert result.error_code == "retry_overflow"
    assert "Unable" in result.data["error"] or result.error


def test_parse_tool_output_preserves_tool_schema_without_intent_defaults() -> None:
    raw = """
    {
      "success": true,
      "tool_name": "send_email",
      "confidence": 0.8,
      "result": {"message_id": "msg-123"},
      "error": null
    }
    """

    result = asyncio.run(parse_output(raw, schema_model=StructuredToolOutput))

    assert result.success is True
    assert result.data["success"] is True
    assert result.data["tool_name"] == "send_email"
    assert "entities" not in result.data
