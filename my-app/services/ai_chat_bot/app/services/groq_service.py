import logging

from groq import AsyncGroq

from app.config.settings import settings
from app.services.language_service import get_language_prompt

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

_groq_client: AsyncGroq | None = None


class GroqServiceError(RuntimeError):
    """Raised when Groq response generation fails."""


def _get_groq_client() -> AsyncGroq:
    """Reuse one async Groq client per process."""
    global _groq_client

    if not settings.groq_api_key:
        raise GroqServiceError("GROQ_API_KEY is not configured")

    if _groq_client is None:
        _groq_client = AsyncGroq(api_key=settings.groq_api_key)

    return _groq_client


async def close_groq_service_client() -> None:
    """Close the shared Groq client during FastAPI shutdown or tests."""
    global _groq_client

    if _groq_client is not None:
        await _groq_client.close()
        _groq_client = None


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
        content = user_message
        if media_context and media_context.get("media_count"):
            content = f"{user_message}\n\nMedia context: {media_context}"

        history_messages = []
        if user_id:
            try:
                from app.tools.memory_tool import get_memory

                raw_history = await get_memory(user_id)
                trimmed_history = raw_history[-10:]
                if trimmed_history and isinstance(trimmed_history[-1], dict) and trimmed_history[-1].get("role") == "user":
                    trimmed_history = trimmed_history[:-1]
                history_messages = [
                    {"role": item["role"], "content": item["content"]}
                    for item in trimmed_history
                    if isinstance(item, dict) and item.get("role") in {"user", "assistant"} and item.get("content")
                ]
            except Exception:
                logger.exception("Conversation memory could not be loaded for user_id=%s", user_id)

        response = await _get_groq_client().chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": f"{SYSTEM_PROMPT}\n\n{get_language_prompt(preferred_language)}"},
                *history_messages,
                {"role": "user", "content": content},
            ],
            temperature=0.4,
            max_tokens=500,
        )
    except Exception as exc:
        logger.exception("Groq response generation failed for user_id=%s", user_id)
        raise GroqServiceError("Failed to generate AI response") from exc

    content = response.choices[0].message.content
    if not content:
        raise GroqServiceError("Groq returned an empty response")

    return content.strip()
