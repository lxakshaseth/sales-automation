import math

import pytest

from app.rag.exceptions.embedding_exceptions import EmbeddingValidationError
from app.rag.models.vector_models import DenseVector, VectorMetadata
from app.rag.services.vector_service import VectorService
from tests.mocks.fake_embeddings import cosine_similarity


@pytest.mark.asyncio
@pytest.mark.unit
async def test_fake_embedding_generation_is_normalized(fake_embedding_generator):
    vector = await fake_embedding_generator.embed_text("WhatsApp automation pricing")

    assert len(vector) == fake_embedding_generator.dimension
    assert math.isclose(math.sqrt(sum(item * item for item in vector)), 1.0, rel_tol=1e-6)
    assert not any(math.isnan(item) for item in vector)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_empty_embedding_input_is_rejected(fake_embedding_generator):
    with pytest.raises(ValueError):
        await fake_embedding_generator.embed_text("")


@pytest.mark.asyncio
@pytest.mark.unit
async def test_multilingual_embeddings_have_valid_dimensions(fake_embedding_generator):
    vectors = await fake_embedding_generator.embed_batch(["pricing", "कीमत", "pricing kya hai"])

    assert len(vectors) == 3
    assert all(len(vector) == 8 for vector in vectors)


@pytest.mark.unit
def test_vector_service_rejects_dimension_mismatch():
    dense = DenseVector(
        vector_id="v1",
        chunk_id="c1",
        document_id="d1",
        embedding_model="fake",
        vector=[0.1, 0.2],
        vector_dimension=3,
        metadata=VectorMetadata(chunk_id="c1", document_id="d1"),
    )

    with pytest.raises(EmbeddingValidationError):
        VectorService().validate_dense_vector(dense)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_semantic_similarity_is_higher_for_related_text(fake_embedding_generator):
    query = await fake_embedding_generator.embed_text("crm pricing automation")
    related = await fake_embedding_generator.embed_text("crm pricing automation")
    unrelated = await fake_embedding_generator.embed_text("cafeteria lunch menu")

    assert cosine_similarity(query, related) > cosine_similarity(query, unrelated)

