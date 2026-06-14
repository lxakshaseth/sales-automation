from dataclasses import dataclass, field

from tests.mocks.fake_embeddings import cosine_similarity


@dataclass
class FakeVectorRecord:
    vector_id: str
    chunk_id: str
    document_id: str
    vector: list[float]
    content: str
    metadata: dict = field(default_factory=dict)


class FakeVectorDB:
    """Deterministic in-memory vector DB for retrieval evaluation tests."""

    def __init__(self) -> None:
        self.records: dict[str, FakeVectorRecord] = {}

    async def add(self, record: FakeVectorRecord) -> None:
        if record.vector_id in self.records:
            raise ValueError("duplicate vector id")
        self.records[record.vector_id] = record

    async def batch_add(self, records: list[FakeVectorRecord]) -> int:
        for record in records:
            await self.add(record)
        return len(records)

    async def search(self, query_vector: list[float], top_k: int = 5) -> list[dict]:
        scored = [
            {
                "vector_id": record.vector_id,
                "chunk_id": record.chunk_id,
                "document_id": record.document_id,
                "score": cosine_similarity(query_vector, record.vector),
                "content": record.content,
                "metadata": record.metadata,
            }
            for record in self.records.values()
        ]
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:top_k]

