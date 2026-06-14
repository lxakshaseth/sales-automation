import json
import re
from typing import Any

from app.config.settings import settings
from app.core.logger import log_error, log_event
from app.intelligence.routing import route_request
from app.models.summary_models import AISummary, LeadAnalysis, TranscriptReport
from app.services.language_service import detect_language

AI_REPORT_SYSTEM_PROMPT = """
You are a senior sales operations analyst.
Return only valid JSON for a professional sales conversation report.
Required JSON keys:
company_name, client_name, client_phone_number, client_email, conversation_source,
language, topic_of_discussion, client_requirements, lead_analysis, ai_remarks,
next_actions, full_conversation_summary.
lead_analysis must include: lead_type, interest_level, buying_intent,
estimated_closing_probability.
Use concise business language. Preserve Hindi, English, or Hinglish meaning.
If a field is missing, infer conservatively or use "Unknown".
""".strip()


class AISummaryServiceError(RuntimeError):
    """Raised when the AI report summary cannot be generated."""


def _extract_json_object(content: str) -> dict[str, Any]:
    """Safely parse strict or slightly noisy LLM JSON output."""
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content or "", flags=re.DOTALL)
        if not match:
            raise
        parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise ValueError("AI output must be a JSON object")
    return parsed


def _list_of_strings(value: Any, fallback: list[str]) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()][:12]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return fallback


def _probability(value: Any) -> int:
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return 0
    return max(0, min(100, number))


def _fallback_ai_summary(
    *,
    company_name: str,
    conversation_source: str,
    phone_number: str,
    transcript: TranscriptReport,
) -> AISummary:
    detected = detect_language(transcript.plain_text or "")
    return AISummary(
        company_name=company_name,
        client_phone_number=phone_number,
        conversation_source=conversation_source,
        language=detected.get("language_name") or "Unknown",
        topic_of_discussion=["Conversation requires manual review"],
        client_requirements=["Review transcript for requirements"],
        lead_analysis=LeadAnalysis(
            lead_type="Needs Review",
            interest_level="Unknown",
            buying_intent="Unknown",
            estimated_closing_probability=0,
        ),
        ai_remarks="AI summary generation was unavailable. Sales team should review the transcript manually.",
        next_actions=["Review conversation transcript", "Follow up with the client"],
        full_conversation_summary=(transcript.plain_text or "No conversation content was available.")[:1500],
    )


async def generate_ai_sales_summary(
    *,
    user_id: str,
    transcript: TranscriptReport,
    company_name: str = "INDUX TECHNOLOGY",
    conversation_source: str = "WhatsApp",
    phone_number: str = "",
    metadata: dict[str, Any] | None = None,
) -> AISummary:
    """Generate a structured sales report summary with Groq."""
    if not transcript.messages:
        return _fallback_ai_summary(
            company_name=company_name,
            conversation_source=conversation_source,
            phone_number=phone_number,
            transcript=transcript,
        )

    payload = {
        "user_id": user_id,
        "company_name": company_name,
        "conversation_source": conversation_source,
        "known_phone_number": phone_number,
        "metadata": metadata or {},
        "transcript": [message.model_dump() for message in transcript.messages],
    }

    try:
        response = await route_request(
            {
                "messages": [
                    {"role": "system", "content": AI_REPORT_SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False, default=str)},
                ],
                "task_type": "summarization",
                "preferred_model": settings.groq_model,
                "temperature": 0.15,
                "max_tokens": 1400,
                "metadata": {"user_id": user_id, "schema": "ai_sales_summary"},
            }
        )
        content = response.content or "{}"
        parsed = _extract_json_object(content)
    except Exception as exc:
        log_error("AI sales report generation failed", user_id=user_id, error_type=type(exc).__name__)
        return _fallback_ai_summary(
            company_name=company_name,
            conversation_source=conversation_source,
            phone_number=phone_number,
            transcript=transcript,
        )

    lead_payload = parsed.get("lead_analysis") if isinstance(parsed.get("lead_analysis"), dict) else {}
    summary = AISummary(
        company_name=str(parsed.get("company_name") or company_name),
        client_name=str(parsed.get("client_name") or "Unknown"),
        client_phone_number=str(parsed.get("client_phone_number") or phone_number),
        client_email=str(parsed.get("client_email") or ""),
        conversation_source=str(parsed.get("conversation_source") or conversation_source),
        language=str(parsed.get("language") or "Unknown"),
        topic_of_discussion=_list_of_strings(parsed.get("topic_of_discussion"), ["Review transcript"]),
        client_requirements=_list_of_strings(parsed.get("client_requirements"), ["Review transcript"]),
        lead_analysis=LeadAnalysis(
            lead_type=str(lead_payload.get("lead_type") or "Needs Review"),
            interest_level=str(lead_payload.get("interest_level") or "Unknown"),
            buying_intent=str(lead_payload.get("buying_intent") or "Unknown"),
            estimated_closing_probability=_probability(lead_payload.get("estimated_closing_probability")),
        ),
        ai_remarks=str(parsed.get("ai_remarks") or ""),
        next_actions=_list_of_strings(parsed.get("next_actions"), ["Follow up with client"]),
        full_conversation_summary=str(parsed.get("full_conversation_summary") or ""),
        raw_ai_payload=parsed,
    )
    log_event(
        "ai_sales_summary_generated",
        user_id=user_id,
        lead_type=summary.lead_analysis.lead_type,
        probability=summary.lead_analysis.estimated_closing_probability,
    )
    return summary
