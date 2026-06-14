from typing import Any

from app.core.logger import log_error, log_event
from app.intelligence.confidence.exceptions import ConfidenceCalculationError
from app.intelligence.confidence.models import ConfidenceReason, ToolConfidence
from app.intelligence.confidence.scoring_service import confidence_bucket


def verify_tool_execution(tool_output: dict[str, Any] | None, tool_exists: bool | None = None, parameters_validated: bool | None = None) -> dict[str, bool]:
    output = tool_output if isinstance(tool_output, dict) else {}
    success = output.get("success") is True
    status = str(output.get("status", "")).lower()
    returned_success_status = success or status in {"success", "ok", "completed", "200"}

    return {
        "tool_exists": bool(tool_exists) if tool_exists is not None else bool(output.get("tool_name") or output.get("name")),
        "parameters_validated": bool(parameters_validated) if parameters_validated is not None else output.get("validation_error") is None,
        "execution_success": success,
        "returned_success_status": returned_success_status,
    }


def verify_tool_response(tool_output: dict[str, Any] | None) -> bool:
    if not isinstance(tool_output, dict) or not tool_output:
        return False
    if tool_output.get("success") is False:
        return False
    response_payload = tool_output.get("result") or tool_output.get("data") or tool_output.get("response")
    return response_payload is not None or tool_output.get("success") is True


async def calculate_tool_confidence(
    tool_output: dict[str, Any] | None = None,
    tool_exists: bool | None = None,
    parameters_validated: bool | None = None,
) -> ToolConfidence:
    log_event("tool_confidence_started")
    try:
        checks = verify_tool_execution(tool_output, tool_exists=tool_exists, parameters_validated=parameters_validated)
        response_complete = verify_tool_response(tool_output)

        if isinstance(tool_output, dict) and tool_output.get("success") is False:
            confidence = 0.0
        else:
            confidence = round(
                (1.0 if checks["tool_exists"] else 0.0) * 0.20
                + (1.0 if checks["parameters_validated"] else 0.0) * 0.20
                + (1.0 if checks["execution_success"] else 0.0) * 0.30
                + (1.0 if checks["returned_success_status"] else 0.0) * 0.15
                + (1.0 if response_complete else 0.0) * 0.15,
                4,
            )

        reasons: list[ConfidenceReason] = []
        if confidence == 1.0:
            reasons.append(ConfidenceReason(code="tool_verified", message="Tool exists, executed successfully, and returned complete output.", weight=1.0, source="tool"))
        else:
            if not checks["tool_exists"]:
                reasons.append(ConfidenceReason(code="tool_missing", message="Requested tool could not be verified.", weight=0.20, source="tool"))
            if not checks["parameters_validated"]:
                reasons.append(ConfidenceReason(code="tool_parameters_invalid", message="Tool parameters were not validated.", weight=0.20, source="tool"))
            if not checks["execution_success"]:
                reasons.append(ConfidenceReason(code="tool_execution_failed", message="Tool execution did not report success.", weight=0.30, source="tool"))
            if not response_complete:
                reasons.append(ConfidenceReason(code="tool_response_incomplete", message="Tool response is missing usable result data.", weight=0.15, source="tool"))

        result = ToolConfidence(
            confidence=confidence,
            confidence_level=confidence_bucket(confidence),
            tool_verified=confidence >= 0.80,
            response_complete=response_complete,
            reasons=reasons,
            **checks,
        )
        log_event("tool_confidence_calculated", confidence=result.confidence, confidence_level=result.confidence_level.value, tool_verified=result.tool_verified)
        return result
    except Exception as exc:
        log_error("Tool confidence calculation failed", exc_info=True, error_type=type(exc).__name__)
        raise ConfidenceCalculationError("tool confidence calculation failed") from exc
