import asyncio
import logging

from app.config.settings import settings
from app.core.performance import measure

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are an intelligent AI sales assistant for a company.

Your job is to:
- talk like a real sales representative
- understand customer intent
- qualify leads
- ask short and smart follow-up questions
- convince users professionally
- book meetings when users show interest
- collect name, requirement, budget, and timeline
- escalate serious customers to human agents

Rules:
- NEVER behave like ChatGPT.
- NEVER give long educational answers unless necessary.
- Keep replies short, natural, and human-like.
- Sound conversational and confident.
- Focus on converting the user into a lead.
- Ask one relevant question at a time.
- If the user asks unrelated educational questions, redirect politely toward business or service discussion.
- Always behave like a sales executive from a company.

Examples:
User: I want to know about machine learning
Assistant: Sure! Are you looking for machine learning development services, learning guidance, or AI automation solutions?

User: I need chatbot for my business
Assistant: Great! What kind of business are you running, and what tasks would you like the chatbot to automate?

User: I am interested
Assistant: Awesome. Can I know your preferred meeting time and your business requirements?
""".strip()

class GroqServiceError(RuntimeError):
    """Raised when Groq response generation fails."""


async def close_groq_service_client() -> None:
    """Compatibility hook; model providers are owned by the routing layer."""


async def generate_sales_reply(
    user_message: str,
    user_id: str | None = None,
    media_context: dict | None = None,
    preferred_language: str = "en",
) -> str:
    """
    Generate an AI sales-assistant reply with Groq.

    This is intentionally isolated so future memory, RAG, queue, or tool-calling
    layers can enrich the message list without changing the Twilio route.
    """
    try:
        from app.security import secure_process_request

        metadata = {"tenant_id": "default", "entrypoint": "generate_sales_reply", "media_context": media_context or {}}
        async with measure("ai", "generate_sales_reply.secured", model=settings.groq_model):
            response = await asyncio.wait_for(
                secure_process_request(
                    {
                        "user_query": user_message,
                        "user_id": user_id,
                        "tenant_id": "default",
                        "channel": "sales_reply",
                        "preferred_language": preferred_language,
                        "system_prompt": SYSTEM_PROMPT,
                        "metadata": metadata,
                        "timeout_seconds": settings.ai_request_timeout_seconds,
                    }
                ),
                timeout=settings.ai_request_timeout_seconds,
            )
    except Exception as exc:
        logger.exception("Secured sales response generation failed for user_id=%s", user_id)
        raise GroqServiceError("Failed to generate secured AI response") from exc

    content = response.response
    if not content:
        raise GroqServiceError("Security orchestrator returned an empty response")

    return content.strip()
