from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.models.context_models import ContextSource


RankingSignal = Literal["query_overlap", "source_score", "importance", "recency", "confidence", "density"]


class RankingWeights(BaseModel):
    query_overlap: float = Field(default=0.35, ge=0.0, le=1.0)
    source_score: float = Field(default=0.25, ge=0.0, le=1.0)
    importance: float = Field(default=0.2, ge=0.0, le=1.0)
    recency: float = Field(default=0.1, ge=0.0, le=1.0)
    confidence: float = Field(default=0.1, ge=0.0, le=1.0)
    min_score: float = Field(default=0.08, ge=0.0, le=1.0)


class RankedContext(BaseModel):
    context_id: str
    source: ContextSource
    content: str
    score: float = Field(ge=0.0, le=1.0)
    rank: int = Field(ge=1)
    token_count: int = Field(default=0, ge=0)
    signals: dict[RankingSignal, float] = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("ranked context content cannot be empty")
        return normalized


class RankingResult(BaseModel):
    ranked_context: list[RankedContext] = Field(default_factory=list)
    dropped_duplicates: int = Field(default=0, ge=0)
    dropped_low_score: int = Field(default=0, ge=0)
    strategy: str = "lexical_semantic_weighted"

