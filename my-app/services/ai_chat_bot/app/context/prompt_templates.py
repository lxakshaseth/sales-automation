from app.models.prompt_models import PromptTemplate


BASE_GUARDRAILS = [
    "Use only the provided context when factual grounding is required.",
    "If context is missing or contradictory, say what is missing instead of guessing.",
    "Preserve user language when practical, including Hindi, English, and Hinglish.",
    "Keep CRM, calendar, WhatsApp, and email facts scoped to the provided context.",
]


CONVERSATIONAL_TEMPLATE = PromptTemplate(
    name="conversational",
    mode="conversational",
    system_template="You are a helpful multilingual AI assistant.",
    user_template="{context}\n\nUser query:\n{query}",
    guardrails=BASE_GUARDRAILS,
)

RAG_QA_TEMPLATE = PromptTemplate(
    name="rag_qa",
    mode="rag_qa",
    system_template=(
        "You answer enterprise knowledge questions with retrieval-grounded reasoning. "
        "Cite the provided source labels when they affect the answer."
    ),
    user_template="{context}\n\nQuestion:\n{query}\n\nAnswer with grounded facts first.",
    guardrails=BASE_GUARDRAILS,
)

MEMORY_AWARE_TEMPLATE = PromptTemplate(
    name="memory_aware",
    mode="memory_aware",
    system_template=(
        "You are a memory-aware assistant. Use recent memory for continuity and long-term memory "
        "for stable preferences, constraints, and business context."
    ),
    user_template="{context}\n\nLatest user message:\n{query}",
    guardrails=BASE_GUARDRAILS,
)

ENTERPRISE_ASSISTANT_TEMPLATE = PromptTemplate(
    name="enterprise_assistant",
    mode="enterprise_assistant",
    system_template=(
        "You are an enterprise AI automation assistant preparing a reliable answer for a user. "
        "Prioritize verified retrieved context, then stable user memory, then recent conversation. "
        "Do not invent facts, actions, appointments, CRM data, or commitments."
    ),
    user_template="{context}\n\nUser query:\n{query}\n\nRespond clearly and safely.",
    guardrails=BASE_GUARDRAILS,
)

TOOL_CALLING_TEMPLATE = PromptTemplate(
    name="tool_calling",
    mode="tool_calling",
    system_template=(
        "You prepare context for a future tool-calling assistant. Distinguish facts, user intent, "
        "constraints, and unknowns. Do not call tools in this layer."
    ),
    user_template="{context}\n\nUser request:\n{query}",
    guardrails=BASE_GUARDRAILS + ["This layer may prepare tool context but must not execute tools."],
)

PROMPT_TEMPLATES = {
    template.name: template
    for template in [
        CONVERSATIONAL_TEMPLATE,
        RAG_QA_TEMPLATE,
        MEMORY_AWARE_TEMPLATE,
        ENTERPRISE_ASSISTANT_TEMPLATE,
        TOOL_CALLING_TEMPLATE,
    ]
}


def get_prompt_template(name: str | None) -> PromptTemplate:
    return PROMPT_TEMPLATES.get(name or "enterprise_assistant", ENTERPRISE_ASSISTANT_TEMPLATE)

