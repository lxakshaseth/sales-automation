from datetime import UTC, datetime, timedelta
from typing import Any

from app.agents.intent_classifier import classify_intent
from app.agents.tool_router import execute_tool
from app.core.logger import log_error, log_event
from app.services.lead_service import build_customer_summary
from app.services.memory_service import get_recent_history, update_workflow_state
from app.services.product_media_service import ProductMediaError, resolve_media_request


def _candidate_slots() -> list[dict[str, str]]:
    now = datetime.now(UTC)
    base = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    slots = []
    for offset in (1, 3, 24):
        start = base + timedelta(hours=offset)
        end = start + timedelta(minutes=30)
        slots.append({"start_time": start.isoformat(), "end_time": end.isoformat()})
    return slots


async def run_workflow(user_id: str, message: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = context or {}
    intent = classify_intent(message)
    log_event("workflow_triggered", user_id=user_id, intent=intent["intent"], confidence=intent["confidence"])

    if intent["intent"] == "meeting_booking":
        slots = _candidate_slots()
        await update_workflow_state(user_id, {"pending_workflow": "meeting_booking", "suggested_slots": slots})
        return {
            "handled": False,
            "intent": intent,
            "workflow": "meeting_booking",
            "suggested_slots": slots,
            "instruction": "Ask the user to pick one of these slots unless they already provided an exact time.",
        }

    if intent["intent"] == "media_request":
        try:
            media = resolve_media_request(message)
        except ProductMediaError as exc:
            log_error("Media request could not be resolved", user_id=user_id, error=str(exc))
            return {"handled": False, "intent": intent, "error": str(exc)}
        if media:
            result = await execute_tool("send_media", {"to": user_id, "query": message})
            log_event("tool_selected", user_id=user_id, tool="send_media", intent=intent["intent"])
            return {"handled": True, "intent": intent, "tool_result": result}

    if intent["intent"] == "lead_qualification":
        history = await get_recent_history(user_id)
        lead_summary = build_customer_summary(user_id, message, history)
        log_event("lead_created", user_id=user_id, lead_stage=lead_summary["lead_stage"], lead_score=lead_summary["lead_score"])
        return {"handled": False, "intent": intent, "lead_summary": lead_summary}

    return {"handled": False, "intent": intent}
