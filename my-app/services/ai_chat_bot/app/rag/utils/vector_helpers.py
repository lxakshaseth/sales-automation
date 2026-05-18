import math

from app.rag.exceptions.embedding_exceptions import EmbeddingValidationError
from app.rag.exceptions.vector_db_exceptions import VectorValidationError


def ensure_valid_vector(vector: list[float], *, expected_dimension: int | None = None) -> None:
    if not vector:
        raise EmbeddingValidationError("embedding vector is empty")

    if expected_dimension is not None and len(vector) != expected_dimension:
        raise EmbeddingValidationError(
            "embedding vector dimension mismatch",
            details={"expected_dimension": expected_dimension, "actual_dimension": len(vector)},
        )

    if any(math.isnan(value) or math.isinf(value) for value in vector):
        raise EmbeddingValidationError("embedding vector contains NaN or infinity")


def vector_l2_norm(vector: list[float]) -> float:
    return math.sqrt(sum(value * value for value in vector))


def ensure_vector_db_vector(vector: list[float], *, expected_dimension: int | None = None) -> None:
    if not vector:
        raise VectorValidationError("vector cannot be empty")

    if expected_dimension is not None and len(vector) != expected_dimension:
        raise VectorValidationError(
            "vector dimension mismatch",
            details={"expected_dimension": expected_dimension, "actual_dimension": len(vector)},
        )

    if any(math.isnan(value) or math.isinf(value) for value in vector):
        raise VectorValidationError("vector contains NaN or infinity")


def l2_normalize_vector(vector: list[float], *, epsilon: float = 1e-12) -> list[float]:
    ensure_vector_db_vector(vector)
    norm = vector_l2_norm(vector)
    if norm <= epsilon:
        raise VectorValidationError("cannot normalize zero vector")
    return [float(value / norm) for value in vector]
