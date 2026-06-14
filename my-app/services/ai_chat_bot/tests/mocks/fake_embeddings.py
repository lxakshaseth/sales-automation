import math


class FakeEmbeddingGenerator:
    """Deterministic multilingual embedding fake."""

    def __init__(self, dimension: int = 8) -> None:
        self.dimension = dimension
        self.keywords = [
            {"whatsapp", "message", "chat", "हिन्दी", "हिंदी"},
            {"crm", "lead", "customer"},
            {"pricing", "price", "cost", "कीमत"},
            {"follow", "follow-up", "automation", "automate"},
            {"calendar", "meeting", "reminder", "slot"},
            {"email", "mail"},
            {"mongo", "redis", "memory"},
            {"cafeteria", "lunch", "menu"},
        ]

    async def embed_text(self, text: str) -> list[float]:
        value = str(text or "").strip()
        if not value:
            raise ValueError("text cannot be empty")
        normalized = value.casefold().replace("-", " ")
        vector = [0.0 for _ in range(self.dimension)]
        for index, terms in enumerate(self.keywords[: self.dimension]):
            vector[index] = float(sum(1 for term in terms if term in normalized))
        if not any(vector):
            for index, char in enumerate(normalized):
                vector[index % self.dimension] += (ord(char) % 17) / 100.0
        norm = math.sqrt(sum(item * item for item in vector)) or 1.0
        return [item / norm for item in vector]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed_text(text) for text in texts]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(a * a for a in left)) or 1.0
    right_norm = math.sqrt(sum(b * b for b in right)) or 1.0
    return numerator / (left_norm * right_norm)
