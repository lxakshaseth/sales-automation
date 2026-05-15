import asyncio

import numpy as np

from app.core.logger import log_event
from app.rag.exceptions.embedding_exceptions import EmbeddingValidationError


class VectorNormalizer:
    """Normalize dense vectors for cosine-similarity-friendly storage."""

    def __init__(self, *, epsilon: float = 1e-12) -> None:
        self.epsilon = epsilon

    async def normalize(self, vector: list[float]) -> list[float]:
        return await asyncio.to_thread(self.normalize_sync, vector)

    def normalize_sync(self, vector: list[float]) -> list[float]:
        array = np.asarray(vector, dtype=np.float32)
        if array.size == 0:
            raise EmbeddingValidationError("cannot normalize empty vector")
        if not np.all(np.isfinite(array)):
            raise EmbeddingValidationError("cannot normalize vector containing NaN or infinity")

        norm = float(np.linalg.norm(array))
        if norm <= self.epsilon:
            raise EmbeddingValidationError("cannot normalize zero vector")

        normalized = array / norm
        result = normalized.astype(float).tolist()
        log_event("rag_vector_normalized", vector_dimension=len(result), l2_norm=round(norm, 6))
        return result

