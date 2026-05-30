from pydantic import BaseModel, Field, field_validator

from app.intelligence.prompts.system_prompts import PROMPT_VERSION, PromptTemplate


class RagChunk(BaseModel):
    content: str
    source: str | None = None
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    chunk_id: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("RAG chunk content cannot be empty")
        return normalized


RAG_GROUNDING_PROMPT = PromptTemplate(
    name="rag_grounding",
    version=PROMPT_VERSION,
    description="Ground answers in retrieved chunks and avoid unsupported claims.",
    template="""
RAG grounding rules:
- Use retrieved chunks as the primary source of truth.
- Prefer higher-confidence chunks and source-labeled evidence.
- If retrieved context is missing, weak, or contradictory, say that the answer could not be verified from the provided context.
- Do not add facts from memory or general knowledge unless clearly marked as not verified by retrieval.
- When sources are available, include compact source labels.
""".strip(),
    tags=["rag", "grounding"],
)

LOW_CONFIDENCE_RAG_FALLBACK = """
Retrieved context is missing or low confidence. Do not guess.
Respond with: "I could not verify this from the available context." Then ask for the missing document, detail, or permission to search again.
""".strip()


def render_rag_context(chunks: list[RagChunk], *, min_confidence: float = 0.35) -> tuple[str, bool]:
    if not chunks:
        return "Retrieved context:\n- None provided", False

    lines: list[str] = []
    high_confidence_found = False
    for index, chunk in enumerate(chunks, start=1):
        source = chunk.source or chunk.chunk_id or "unknown"
        high_confidence_found = high_confidence_found or chunk.score >= min_confidence
        lines.append(f"[RAG:{index}] score={chunk.score:.2f} source={source} :: {chunk.content}")

    return "Retrieved context:\n" + "\n".join(f"- {line}" for line in lines), high_confidence_found

