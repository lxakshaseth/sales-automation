import time

from app.core.logger import log_error, log_event
from app.rag.exceptions.embedding_exceptions import BatchEmbeddingError, EmbeddingError
from app.rag.models.document_models import DocumentChunk
from app.rag.models.embedding_models import BatchEmbeddingResult, EmbeddingConfig
from app.rag.models.vector_models import DenseVector
from app.rag.utils.batch_helpers import batched
from app.rag.utils.embedding_helpers import build_embedding_cache_key


class BatchEmbedder:
    """Memory-safe batch embedding processor with cache-aware generation."""

    MAX_BATCH_SIZE = 512

    def __init__(self, *, embedding_service) -> None:
        self.embedding_service = embedding_service

    async def embed_chunks(self, chunks: list[DocumentChunk], config: EmbeddingConfig) -> BatchEmbeddingResult:
        started_at = time.perf_counter()
        if config.batch_size > self.MAX_BATCH_SIZE:
            error = BatchEmbeddingError(
                "batch size too large",
                details={"batch_size": config.batch_size, "max_batch_size": self.MAX_BATCH_SIZE},
            )
            return BatchEmbeddingResult(success=False, errors=[error.to_response()], total_chunks=len(chunks), config=config)

        vectors: list[DenseVector] = []
        errors: list[dict[str, object]] = []
        cached_count = 0
        generated_count = 0

        log_event("rag_embedding_batch_started", total_chunks=len(chunks), batch_size=config.batch_size)

        for batch_index, chunk_batch in enumerate(batched(chunks, config.batch_size)):
            try:
                uncached_chunks: list[DocumentChunk] = []
                cache_keys: dict[str, str] = {}

                for chunk in chunk_batch:
                    cache_key = build_embedding_cache_key(chunk, config)
                    cache_keys[chunk.chunk_id] = cache_key
                    cached = await self.embedding_service.cache.get(cache_key) if config.cache_enabled else None
                    if cached is not None:
                        vectors.append(cached)
                        cached_count += 1
                    else:
                        uncached_chunks.append(chunk)

                if uncached_chunks:
                    generated_vectors = await self.embedding_service._embed_uncached_batch(uncached_chunks, config)
                    for chunk, vector in zip(uncached_chunks, generated_vectors, strict=True):
                        if config.cache_enabled:
                            await self.embedding_service.cache.set(cache_keys[chunk.chunk_id], vector)
                        vectors.append(vector)
                        generated_count += 1

                log_event(
                    "rag_embedding_batch_processed",
                    batch_index=batch_index,
                    batch_size=len(chunk_batch),
                    generated_count=generated_count,
                    cached_count=cached_count,
                )
            except EmbeddingError as exc:
                log_error("RAG embedding batch failed", batch_index=batch_index, error_code=exc.error_code)
                errors.append(exc.to_response() | {"batch_index": batch_index})
            except Exception as exc:
                log_error("Unexpected RAG embedding batch failure", batch_index=batch_index, error_type=type(exc).__name__)
                error = BatchEmbeddingError(details={"batch_index": batch_index, "error_type": type(exc).__name__})
                errors.append(error.to_response())

        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        log_event(
            "rag_embedding_batch_completed",
            total_chunks=len(chunks),
            vector_count=len(vectors),
            error_count=len(errors),
            cached_count=cached_count,
            generated_count=generated_count,
            duration_ms=duration_ms,
        )

        return BatchEmbeddingResult(
            success=not errors,
            vectors=vectors,
            errors=errors,
            cached_count=cached_count,
            generated_count=generated_count,
            total_chunks=len(chunks),
            duration_ms=duration_ms,
            config=config,
        )

