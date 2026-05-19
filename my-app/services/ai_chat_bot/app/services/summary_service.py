import json
from typing import Any

from app.core.event_bus import EVENT_SUMMARY_GENERATED, emit_event
from app.core.logger import log_error, log_event
from app.services.groq_service import GroqServiceError, _get_groq_client
from app.config.settings import settings
from app.services.language_service import detect_language


SUMMARY_SYSTEM_PROMPT = """
You summarize closed sales chatbot conversations for a business owner.
Return only valid JSON with these string fields:
customer_intent, summary, lead_quality, recommended_action.
Be concise, practical, and sales-focused.
Write customer-facing summary text in the detected conversation language when it is English, Hindi, or Marathi.
""".strip()


class SummaryServiceError(RuntimeError):
    """Raised when the AI summary cannot be generated."""


def _fallback_summary(history: list[Any]) -> dict[str, str]:
    text = " ".join(str(item.get("content", item)) if isinstance(item, dict) else str(item) for item in history)
    return {
        "customer_intent": "Unknown",
        "summary": text[:700] or "No conversation content was available.",
        "lead_quality": "Unqualified",
        "recommended_action": "Review the conversation manually.",
    }


def _parse_summary(content: str, history: list[Any]) -> dict[str, str]:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return _fallback_summary(history) | {"summary": content.strip()[:700]}

    if not isinstance(parsed, dict):
        return _fallback_summary(history)

    return {
        "customer_intent": str(parsed.get("customer_intent", "")),
        "summary": str(parsed.get("summary", "")),
        "lead_quality": str(parsed.get("lead_quality", "")),
        "recommended_action": str(parsed.get("recommended_action", "")),
    }


async def generate_conversation_summary(user_id: str, history: list[Any]) -> dict[str, str]:
    """
    Generate the close-chat lead summary with Groq.

    The prompt requests strict JSON; parsing is defensive because production LLM
    responses can still occasionally include extra text.
    """
    if not history:
        summary = _fallback_summary(history)
    else:
        history_text = " ".join(str(item.get("content", item)) if isinstance(item, dict) else str(item) for item in history)
        detected_language = detect_language(history_text)
        try:
            response = await _get_groq_client().chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "conversation_language": detected_language["language_name"],
                                "history": history,
                            },
                            ensure_ascii=False,
                        ),
                    },
                ],
                temperature=0.2,
                max_tokens=500,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "{}"
            summary = _parse_summary(content, history)
        except GroqServiceError:
            raise
        except Exception as exc:
            log_error("AI summary generation failed", user_id=user_id, error_type=type(exc).__name__)
            raise SummaryServiceError("failed to generate conversation summary") from exc

    log_event("summary_generated", user_id=user_id, lead_quality=summary.get("lead_quality"))
    await emit_event(EVENT_SUMMARY_GENERATED, {"user_id": user_id, "summary": summary}, handle_local=True)
    return summary
