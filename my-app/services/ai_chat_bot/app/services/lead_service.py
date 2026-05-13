import re
from typing import Any

from app.core.logger import log_event

LEAD_STAGES = {"new", "interested", "meeting_booked", "converted", "inactive"}


def score_lead(message: str, history: list[Any] | None = None) -> dict[str, Any]:
    text = " ".join(
        [
            str(message or ""),
            *[
                str(item.get("content", ""))
                for item in history or []
                if isinstance(item, dict)
            ],
        ]
    ).lower()
    score = 10
    signals = []
    weighted_signals = {
        "budget": 15,
        "price": 10,
        "demo": 15,
        "meeting": 20,
        "call": 15,
        "interested": 20,
        "buy": 25,
        "need": 10,
        "urgent": 20,
    }
    for signal, weight in weighted_signals.items():
        if signal in text:
            score += weight
            signals.append(signal)
    email_present = bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text))
    phone_present = bool(re.search(r"(?:\+?\d[\s-]?){8,}", text))
    if email_present:
        score += 15
        signals.append("email")
    if phone_present:
        score += 10
        signals.append("phone")
    score = min(100, score)
    if score >= 70:
        stage = "interested"
    elif score <= 20:
        stage = "new"
    else:
        stage = "new"
    return {"score": score, "stage": stage, "signals": sorted(set(signals))}


def recommended_next_action(analysis: dict[str, Any]) -> str:
    score = int(analysis.get("score") or 0)
    signals = set(analysis.get("signals") or [])
    if "meeting" in signals or "demo" in signals or score >= 75:
        return "Offer two meeting slots and create a CRM lead."
    if score >= 45:
        return "Ask one qualifying question about requirement, budget, or timeline."
    return "Continue discovery and collect the customer's business need."


def build_customer_summary(user_id: str, message: str, history: list[Any] | None = None) -> dict[str, Any]:
    analysis = score_lead(message, history)
    summary = {
        "user_id": user_id,
        "lead_stage": analysis["stage"],
        "lead_score": analysis["score"],
        "signals": analysis["signals"],
        "customer_summary": str(message or "")[:500],
        "recommended_next_action": recommended_next_action(analysis),
    }
    log_event("lead_analyzed", **summary)
    return summary
