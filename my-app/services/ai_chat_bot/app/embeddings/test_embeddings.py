from app.rag.embeddings.embedding_service import (
    EmbeddingService
)


def test_embedding_generation():

    service = EmbeddingService()

    vector = service.generate_embedding(
        "refund policy"
    )

    assert vector is not None

    assert len(vector) == 384