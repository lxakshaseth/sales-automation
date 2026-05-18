import math

from app.rag.utils.vector_helpers import vector_l2_norm


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    denominator = vector_l2_norm(left) * vector_l2_norm(right)
    if denominator == 0:
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=True)) / denominator


def euclidean_distance(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        return math.inf
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right, strict=True)))


def dot_product(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=True))


def faiss_score_to_similarity(raw_score: float, metric: str) -> tuple[float, float | None]:
    if metric == "cosine":
        return float(raw_score), None
    if metric == "l2":
        distance = float(raw_score)
        return 1.0 / (1.0 + distance), distance
    if metric == "dot_product":
        return float(raw_score), None
    return float(raw_score), None
