import asyncio
import time

from app.core.logger import log_error, log_event
from app.rag.embeddings.embedding_cache import EmbeddingCache
from app.rag.embeddings.vector_normalizer import VectorNormalizer
from app.rag.exceptions.embedding_exceptions import EmbeddingError, EmbeddingGenerationError, EmptyChunkError
from app.rag.models.document_models import DocumentChunk
from app.rag.models.embedding_models import BatchEmbeddingResult, EmbeddingConfig, EmbeddingResponse
from app.rag.models.vector_models import DenseVector, VectorMetadata
from app.rag.services.model_loader_service import ModelLoaderService
from app.rag.utils.embedding_helpers import build_embedding_cache_key, build_vector_id, prepare_embedding_text
from app.rag.utils.vector_helpers import ensure_valid_vector


class EmbeddingService:
    """Generate validated, normalized dense vectors from R2 document chunks."""

    def __init__(
        self,
        *,
        model_loader: ModelLoaderService | None = None,
        normalizer: VectorNormalizer | None = None,
        cache: EmbeddingCache | None = None,
    ) -> None:
        self.model_loader = model_loader or ModelLoaderService()
        self.normalizer = normalizer or VectorNormalizer()
        self.cache = cache or EmbeddingCache()

    async def generate_embedding(
        self,
        chunk: DocumentChunk,
        config: EmbeddingConfig | None = None,
    ) -> EmbeddingResponse:
        started_at = time.perf_counter()
        resolved_config = config or EmbeddingConfig()

        try:
            cache_key = build_embedding_cache_key(chunk, resolved_config)
            if resolved_config.cache_enabled:
                cached_vector = await self.cache.get(cache_key)
                if cached_vector is not None:
                    return EmbeddingResponse(
                        success=True,
                        vector=cached_vector,
                        cached=True,
                        duration_ms=self._duration_ms(started_at),
                    )

            vectors = await self._embed_uncached_batch([chunk], resolved_config)
            vector = vectors[0]
            if resolved_config.cache_enabled:
                await self.cache.set(cache_key, vector)

            log_event(
                "rag_embedding_generated",
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                model_name=resolved_config.model_name,
                vector_dimension=vector.vector_dimension,
                duration_ms=self._duration_ms(started_at),
            )
            return EmbeddingResponse(success=True, vector=vector, duration_ms=self._duration_ms(started_at))
        except EmbeddingError as exc:
            log_error("RAG embedding generation failed", chunk_id=chunk.chunk_id, error_code=exc.error_code)
            return EmbeddingResponse(success=False, error=exc.to_response(), duration_ms=self._duration_ms(started_at))
        except Exception as exc:
            log_error("Unexpected RAG embedding failure", chunk_id=chunk.chunk_id, error_type=type(exc).__name__, exc_info=True)
            error = EmbeddingGenerationError(details={"chunk_id": chunk.chunk_id, "error_type": type(exc).__name__})
            return EmbeddingResponse(success=False, error=error.to_response(), duration_ms=self._duration_ms(started_at))

    async def generate_embeddings_batch(
        self,
        chunks: list[DocumentChunk],
        config: EmbeddingConfig | None = None,
    ) -> BatchEmbeddingResult:
        from app.rag.embeddings.batch_embedder import BatchEmbedder

        return await BatchEmbedder(embedding_service=self).embed_chunks(chunks, config or EmbeddingConfig())

    def validate_embedding(self, vector: list[float], *, expected_dimension: int | None = None) -> None:
        ensure_valid_vector(vector, expected_dimension=expected_dimension)

    async def normalize_embedding(self, vector: list[float]) -> list[float]:
        return await self.normalizer.normalize(vector)

    async def _embed_uncached_batch(self, chunks: list[DocumentChunk], config: EmbeddingConfig) -> list[DenseVector]:
        prepared_texts: list[str] = []
        valid_chunks: list[DocumentChunk] = []

        for chunk in chunks:
            text = prepare_embedding_text(chunk.content)
            if not text:
                raise EmptyChunkError("chunk content is empty", details={"chunk_id": chunk.chunk_id})
            prepared_texts.append(text)
            valid_chunks.append(chunk)

        model = await self.model_loader.get_embedding_model(config)

        try:
            raw_embeddings = await asyncio.to_thread(
                model.encode,
                prepared_texts,
                batch_size=min(config.batch_size, len(prepared_texts)),
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=False,
            )
        except RuntimeError as exc:
            raise EmbeddingGenerationError(
                "embedding model runtime failure",
                details={"model_name": config.model_name, "error_type": type(exc).__name__},
            ) from exc
        except Exception as exc:
            raise EmbeddingGenerationError(
                "embedding model encode failure",
                details={"model_name": config.model_name, "error_type": type(exc).__name__},
            ) from exc

        dense_vectors: list[DenseVector] = []
        for chunk, raw_embedding in zip(valid_chunks, raw_embeddings, strict=True):
            vector = [float(value) for value in raw_embedding.tolist()]
            if config.normalize:
                vector = await self.normalize_embedding(vector)

            self.validate_embedding(vector, expected_dimension=config.expected_dimension)
            dense_vectors.append(self._build_dense_vector(chunk, vector, config))

        log_event(
            "rag_embedding_batch_generated",
            model_name=config.model_name,
            chunk_count=len(dense_vectors),
            vector_dimension=config.expected_dimension,
        )
        return dense_vectors

    def _build_dense_vector(self, chunk: DocumentChunk, vector: list[float], config: EmbeddingConfig) -> DenseVector:
        metadata = VectorMetadata(
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            source_filename=chunk.document_metadata.filename,
            chunk_index=chunk.chunk_index,
            token_count=chunk.token_count,
            page_number=chunk.page_number,
            embedding_provider="sentence-transformers",
            embedding_version=config.model_name,
            extra={
                "chunk_strategy": chunk.strategy,
                "source_section_index": chunk.source_section_index,
                "chunk_metadata": chunk.metadata,
            },
        )
        return DenseVector(
            vector_id=build_vector_id(chunk, config.model_name),
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            embedding_model=config.model_name,
            vector=vector,
            vector_dimension=len(vector),
            normalized=config.normalize,
            metadata=metadata,
        )

    def _duration_ms(self, started_at: float) -> float:
        return round((time.perf_counter() - started_at) * 1000, 2)

