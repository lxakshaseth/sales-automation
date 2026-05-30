from app.intelligence.prompts.system_prompts import PROMPT_VERSION, PromptTemplate

CRM_PROMPTS: dict[str, PromptTemplate] = {
    "lead_qualification": PromptTemplate(
        name="lead_qualification",
        version=PROMPT_VERSION,
        description="Qualify leads from conversation and CRM context.",
        template="""
CRM lead qualification:
- Identify buyer intent, use case, company context, budget signals, timeline, authority, and urgency.
- Mark unsupported fields as null.
- Do not inflate lead score without explicit evidence.
- Support English, Hindi, and Hinglish conversations.
""".strip(),
        tags=["crm", "lead-scoring"],
    ),
    "hot_lead_detection": PromptTemplate(
        name="hot_lead_detection",
        version=PROMPT_VERSION,
        description="Detect high-intent sales opportunities.",
        template="""
Hot lead detection:
- Strong signals include pricing requests, demo requests, implementation timeline, budget readiness, decision-maker role, and repeated follow-up.
- Weak signals include generic learning questions or vague curiosity.
- Return evidence snippets for every hot-lead reason.
""".strip(),
        tags=["crm", "sales-intent"],
    ),
    "crm_note_generation": PromptTemplate(
        name="crm_note_generation",
        version=PROMPT_VERSION,
        description="Generate structured CRM notes.",
        template="""
CRM note format:
- Summary: concise conversation summary.
- Need: user's business requirement.
- Intent: sales/support/general.
- Next step: recommended follow-up.
- Missing info: fields still needed.
Use only verified conversation and CRM context.
""".strip(),
        tags=["crm", "notes"],
    ),
    "followup_recommendation": PromptTemplate(
        name="followup_recommendation",
        version=PROMPT_VERSION,
        description="Recommend next best sales follow-up.",
        template="""
Follow-up recommendation:
- Recommend timing, channel, message angle, and required owner action.
- Base urgency on explicit user intent and CRM history.
- Do not promise a follow-up has been scheduled unless a scheduler tool result confirms it.
""".strip(),
        tags=["crm", "follow-up"],
    ),
}


def get_crm_prompt(name: str) -> PromptTemplate:
    return CRM_PROMPTS.get(name, CRM_PROMPTS["lead_qualification"])

