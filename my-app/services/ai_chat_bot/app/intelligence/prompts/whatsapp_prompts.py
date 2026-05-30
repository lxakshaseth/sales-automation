from typing import Literal

from app.intelligence.prompts.system_prompts import PROMPT_VERSION, PromptTemplate

WhatsAppLanguage = Literal["english", "hindi", "hinglish", "auto"]

WHATSAPP_PROMPT = PromptTemplate(
    name="whatsapp_conversation",
    version=PROMPT_VERSION,
    description="Short mobile-friendly WhatsApp response style.",
    template="""
WhatsApp response style:
- Keep replies short, natural, and mobile-friendly.
- Use the user's language style: English, Hindi, or Hinglish.
- Ask one clear question at a time when qualification is needed.
- Emojis are allowed only when they fit the user's tone; never overuse them.
- Avoid long paragraphs, markdown tables, and corporate-heavy wording.
""".strip(),
    tags=["whatsapp", "mobile", "multilingual"],
)


LANGUAGE_STYLE_PROMPTS: dict[str, str] = {
    "english": "Reply in clear, natural English.",
    "hindi": "Reply in natural Hindi while preserving names, products, and technical terms.",
    "hinglish": "Reply in natural Hinglish, matching the user's casual Hindi-English mix.",
    "auto": "Detect whether English, Hindi, or Hinglish fits the latest user message and reply in that style.",
}


def get_whatsapp_language_prompt(language: str | None = "auto") -> str:
    return LANGUAGE_STYLE_PROMPTS.get((language or "auto").lower(), LANGUAGE_STYLE_PROMPTS["auto"])

