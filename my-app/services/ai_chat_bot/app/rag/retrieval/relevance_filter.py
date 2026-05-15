from app.core.logger import log_event
from app.rag.models.ranking_models import RankedChunk


class RelevanceFilter:
    """Remove weak/noisy context before it reaches future prompt construction."""

    def __init__(self, *, default_threshold: float = 0.65) -> None:
        self.default_threshold = default_threshold

    async def filter(self, chunks: list[RankedChunk], *, threshold: float | None = None, top_k: int = 5) -> list[RankedChunk]:
        resolved_threshold = self.default_threshold if threshold is None else threshold
        filtered = [chunk for chunk in chunks if chunk.final_score >= resolved_threshold]
        filtered = filtered[:top_k]
        filtered = [chunk.model_copy(update={"rank": index + 1}) for index, chunk in enumerate(filtered)]
        log_event(
            "rag_relevance_filter_completed",
            input_count=len(chunks),
            output_count=len(filtered),
            threshold=resolved_threshold,
        )
        return filtered
