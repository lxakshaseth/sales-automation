from app.rag.embeddings.vector_normalizer import VectorNormalizer
from app.rag.exceptions.embedding_exceptions import EmbeddingValidationError
from app.rag.models.vector_models import DenseVector
from app.rag.utils.vector_helpers import ensure_valid_vector


class VectorService:
    """
    Vector utility service for R3.

    This does not store vectors or perform retrieval. It only validates and
    normalizes vectors so future vector DB adapters receive consistent data.
    """

    def __init__(self, *, normalizer: VectorNormalizer | None = None) -> None:
        self.normalizer = normalizer or VectorNormalizer()

    async def normalize_vector(self, vector: list[float]) -> list[float]:
        return await self.normalizer.normalize(vector)

    def validate_dense_vector(self, dense_vector: DenseVector, *, expected_dimension: int | None = None) -> None:
        if dense_vector.vector_dimension != len(dense_vector.vector):
            raise EmbeddingValidationError(
                "dense vector dimension metadata mismatch",
                details={"vector_dimension": dense_vector.vector_dimension, "actual_dimension": len(dense_vector.vector)},
            )
        ensure_valid_vector(dense_vector.vector, expected_dimension=expected_dimension)

