from typing import Literal

from app.intelligence.prompts.system_prompts import PROMPT_VERSION, PromptTemplate

EmailTone = Literal["formal", "friendly", "sales", "enterprise"]

EMAIL_PROMPTS: dict[str, PromptTemplate] = {
    "email_draft": PromptTemplate(
        name="email_draft",
        version=PROMPT_VERSION,
        description="Draft professional emails with tone control.",
        template="""
Email drafting rules:
- Write a clear subject and concise body.
- Match the requested tone: formal, friendly, sales, or enterprise.
- Preserve facts from CRM, transcript, and user instructions.
- Do not state that the email was sent; drafting is not sending.
""".strip(),
        tags=["email", "drafting"],
    ),
    "followup_email": PromptTemplate(
        name="followup_email",
        version=PROMPT_VERSION,
        description="Generate follow-up emails after sales or support conversations.",
        template="""
Follow-up email rules:
- Mention the discussed requirement, next step, and any agreed timeline only if verified.
- Keep the CTA specific and professional.
- If details are missing, use a neutral placeholder or ask for the missing detail.
""".strip(),
        tags=["email", "follow-up"],
    ),
    "transcript_email": PromptTemplate(
        name="transcript_email",
        version=PROMPT_VERSION,
        description="Format conversation transcripts for email.",
        template="""
Transcript email rules:
- Summarize key points first, then include a readable transcript section if requested.
- Redact secrets, OTPs, passwords, and private tokens.
- Keep multilingual text Unicode-safe and do not mistranslate names.
""".strip(),
        tags=["email", "transcript"],
    ),
}


TONE_PROMPTS: dict[str, str] = {
    "formal": "Use a polished formal tone with precise wording.",
    "friendly": "Use a warm professional tone without being casual.",
    "sales": "Use a persuasive sales tone with a clear CTA and no exaggerated claims.",
    "enterprise": "Use an executive enterprise tone focused on outcomes, risk, and next steps.",
}


def get_email_prompt(name: str = "email_draft", tone: str = "enterprise") -> str:
    template = EMAIL_PROMPTS.get(name, EMAIL_PROMPTS["email_draft"]).template
    tone_prompt = TONE_PROMPTS.get(tone, TONE_PROMPTS["enterprise"])
    return f"{template}\n{tone_prompt}"

