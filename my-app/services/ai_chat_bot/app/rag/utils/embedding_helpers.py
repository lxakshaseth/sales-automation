import hashlib
import re

from app.rag.models.document_models import DocumentChunk
from app.rag.models.embedding_models import EmbeddingConfig


CONTROL_CHARACTER_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def prepare_embedding_text(text: str) -> str:
    """Unicode-safe cleanup before sending text to an embedding model."""

    value = CONTROL_CHARACTER_PATTERN.sub("", str(text or ""))
    return value.strip()


def build_embedding_cache_key(chunk: DocumentChunk, config: EmbeddingConfig) -> str:
    payload = "|".join(
        [
            chunk.chunk_id,
            chunk.document_id,
            config.model_name,
            str(config.expected_dimension),
            str(config.normalize),
            hashlib.sha256(chunk.content.encode("utf-8", errors="replace")).hexdigest(),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_vector_id(chunk: DocumentChunk, model_name: str) -> str:
    model_hash = hashlib.sha1(model_name.encode("utf-8")).hexdigest()[:10]
    return f"{chunk.document_id}:{chunk.chunk_id}:{model_hash}"

