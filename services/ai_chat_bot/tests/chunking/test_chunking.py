import pytest

from app.rag.chunking.recursive_chunker import RecursiveDocumentChunker
from app.rag.chunking.token_chunker import TokenAwareChunker, estimate_token_count
from app.rag.models.document_models import DocumentSection


@pytest.mark.asyncio
@pytest.mark.unit
async def test_recursive_chunking_keeps_chunks_token_safe(raw_document):
    content = " ".join(["sales automation"] * 120)
    document = raw_document.model_copy(
        update={
            "content": content,
            "sections": [DocumentSection(index=0, content=content, section_type="body")],
        }
    )
    chunker = RecursiveDocumentChunker(chunk_size_tokens=40, chunk_overlap_tokens=8)

    result = await chunker.chunk_document(document)

    assert result.success is True
    assert result.chunk_count > 1
    assert all(chunk.token_count <= 45 for chunk in result.chunks)
    assert all(chunk.strategy == "recursive" for chunk in result.chunks)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_token_chunking_validates_overlap_and_prevents_empty_chunks(raw_document):
    chunker = TokenAwareChunker(chunk_size_tokens=10, chunk_overlap_tokens=3)

    result = await chunker.chunk_document(raw_document)

    assert result.success is True
    assert all(chunk.content.strip() for chunk in result.chunks)
    assert all(chunk.overlap_previous_tokens <= 3 for chunk in result.chunks)


@pytest.mark.unit
def test_invalid_chunk_overlap_is_rejected():
    with pytest.raises(ValueError):
        TokenAwareChunker(chunk_size_tokens=10, chunk_overlap_tokens=10)


@pytest.mark.unit
def test_token_counter_supports_hindi_and_hinglish(multilingual_text: str):
    assert estimate_token_count(multilingual_text) >= 8
    assert estimate_token_count("नमस्ते pricing kya hai?") >= 4
