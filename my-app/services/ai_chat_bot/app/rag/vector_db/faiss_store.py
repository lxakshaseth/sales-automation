import asyncio
from pathlib import Path

import numpy as np

from app.core.logger import log_error, log_event
from app.rag.exceptions.vector_db_exceptions import DuplicateVectorError, MissingVectorError, VectorIndexError, VectorPersistenceError, VectorSearchError
from app.rag.models.search_models import SearchQuery, SearchResult
from app.rag.models.vector_models import DenseVector, StoredVector, VectorIndexConfig
from app.rag.utils.faiss_helpers import ensure_index_directory, faiss_index_file, import_faiss
from app.rag.utils.search_helpers import apply_score_threshold, metadata_matches
from app.rag.utils.vector_helpers import ensure_vector_db_vector, l2_normalize_vector
from app.rag.vector_db.similarity_metrics import faiss_score_to_similarity
from app.rag.vector_db.vector_serializer import VectorSerializer


class FAISSVectorStore:
    """Local FAISS-backed vector store with persistent metadata mappings."""

    def __init__(self, config: VectorIndexConfig | None = None) -> None:
        self.config = config or VectorIndexConfig()
        self.serializer = VectorSerializer(index_path=self.config.index_path, index_name=self.config.index_name)
        self._index = None
        self._loaded = False
        self._lock = asyncio.Lock()
        self.id_to_row: dict[str, int] = {}
        self.row_to_id: dict[int, str] = {}
        self.vectors: dict[str, StoredVector] = {}

    @property
    def size(self) -> int:
        return len(self.vectors)

    async def initialize(self) -> None:
        async with self._lock:
            if self._loaded:
                return
            await asyncio.to_thread(self._initialize_sync)
            self.id_to_row, self.row_to_id, self.vectors = await self.serializer.load()
            self._loaded = True
            log_event(
                "rag_faiss_index_loaded",
                index_name=self.config.index_name,
                vector_count=len(self.vectors),
                vector_dimension=self.config.vector_dimension,
            )

    def _initialize_sync(self) -> None:
        faiss = import_faiss()
        ensure_index_directory(self.config.index_path)
        index_file = faiss_index_file(self.config.index_path, self.config.index_name)

        try:
            if index_file.exists():
                self._index = faiss.read_index(str(index_file))
                return

            if self.config.similarity_metric in {"cosine", "dot_product"}:
                self._index = faiss.IndexFlatIP(self.config.vector_dimension)
            elif self.config.similarity_metric == "l2":
                self._index = faiss.IndexFlatL2(self.config.vector_dimension)
            else:
                raise VectorIndexError("unsupported similarity metric", details={"metric": self.config.similarity_metric})

            log_event(
                "rag_faiss_index_created",
                index_name=self.config.index_name,
                vector_dimension=self.config.vector_dimension,
                similarity_metric=self.config.similarity_metric,
            )
        except VectorIndexError:
            raise
        except Exception as exc:
            raise VectorIndexError("failed to initialize FAISS index", details={"index_name": self.config.index_name}) from exc

    async def add_vector(self, dense_vector: DenseVector) -> StoredVector:
        result = await self.add_vectors([dense_vector])
        if not result:
            raise VectorIndexError("vector was not inserted", details={"vector_id": dense_vector.vector_id})
        return result[0]

    async def add_vectors(self, dense_vectors: list[DenseVector]) -> list[StoredVector]:
        await self.initialize()
        async with self._lock:
            return await asyncio.to_thread(self._add_vectors_sync, dense_vectors)

    def _add_vectors_sync(self, dense_vectors: list[DenseVector]) -> list[StoredVector]:
        if self._index is None:
            raise VectorIndexError("FAISS index is not initialized")
        if not dense_vectors:
            return []

        matrix_rows: list[list[float]] = []
        stored: list[StoredVector] = []
        next_row = len(self.row_to_id)

        for dense_vector in dense_vectors:
            if dense_vector.vector_id in self.vectors:
                raise DuplicateVectorError("duplicate vector id", details={"vector_id": dense_vector.vector_id})

            vector = list(dense_vector.vector)
            ensure_vector_db_vector(vector, expected_dimension=self.config.vector_dimension)
            if self.config.normalize_on_insert and self.config.similarity_metric in {"cosine", "dot_product"} and not dense_vector.normalized:
                vector = l2_normalize_vector(vector)

            row_id = next_row + len(stored)
            stored_vector = StoredVector(
                vector_id=dense_vector.vector_id,
                chunk_id=dense_vector.chunk_id,
                document_id=dense_vector.document_id,
                embedding_model=dense_vector.embedding_model,
                vector_dimension=dense_vector.vector_dimension,
                normalized=dense_vector.normalized or self.config.normalize_on_insert,
                metadata=dense_vector.metadata,
                storage_index=row_id,
            )
            matrix_rows.append(vector)
            stored.append(stored_vector)

        matrix = np.asarray(matrix_rows, dtype=np.float32)
        self._index.add(matrix)

        for stored_vector in stored:
            row_id = int(stored_vector.storage_index or 0)
            self.vectors[stored_vector.vector_id] = stored_vector
            self.id_to_row[stored_vector.vector_id] = row_id
            self.row_to_id[row_id] = stored_vector.vector_id

        log_event("rag_faiss_vectors_inserted", index_name=self.config.index_name, inserted_count=len(stored), total_vectors=len(self.vectors))
        return stored

    async def search(self, query: SearchQuery) -> list[SearchResult]:
        await self.initialize()
        async with self._lock:
            return await asyncio.to_thread(self._search_sync, query)

    def _search_sync(self, query: SearchQuery) -> list[SearchResult]:
        if self._index is None:
            raise VectorSearchError("FAISS index is not initialized")
        ensure_vector_db_vector(query.query_vector, expected_dimension=self.config.vector_dimension)
        if self.size == 0:
            return []

        vector = list(query.query_vector)
        if self.config.normalize_on_insert and self.config.similarity_metric in {"cosine", "dot_product"}:
            vector = l2_normalize_vector(vector)

        matrix = np.asarray([vector], dtype=np.float32)
        search_k = min(max(query.top_k * 3, query.top_k), self.size)

        try:
            raw_scores, raw_indices = self._index.search(matrix, search_k)
        except Exception as exc:
            log_error("RAG FAISS search failed", index_name=self.config.index_name, error_type=type(exc).__name__)
            raise VectorSearchError("FAISS search failed", details={"index_name": self.config.index_name}) from exc

        results: list[SearchResult] = []
        for raw_rank, (raw_score, row_index) in enumerate(zip(raw_scores[0], raw_indices[0], strict=True), start=1):
            if row_index < 0:
                continue
            vector_id = self.row_to_id.get(int(row_index))
            if vector_id is None:
                continue
            stored_vector = self.vectors.get(vector_id)
            if stored_vector is None or not metadata_matches(stored_vector, query.metadata_filter):
                continue

            score, distance = faiss_score_to_similarity(float(raw_score), self.config.similarity_metric)
            results.append(
                SearchResult(
                    vector_id=stored_vector.vector_id,
                    chunk_id=stored_vector.chunk_id,
                    document_id=stored_vector.document_id,
                    score=score,
                    distance=distance,
                    rank=len(results) + 1,
                    stored_vector=stored_vector,
                    metadata={"raw_rank": raw_rank, "similarity_metric": self.config.similarity_metric},
                )
            )
            if len(results) >= query.top_k:
                break

        return apply_score_threshold(results, query.score_threshold)

    async def get_vector_by_id(self, vector_id: str) -> StoredVector:
        await self.initialize()
        stored = self.vectors.get(vector_id)
        if stored is None:
            raise MissingVectorError("vector mapping not found", details={"vector_id": vector_id})
        return stored

    async def remove_vector(self, vector_id: str) -> None:
        await self.initialize()
        raise VectorIndexError(
            "FAISS IndexFlat does not support in-place deletion; rebuild index without this vector",
            details={"vector_id": vector_id, "operation": "remove_vector"},
        )

    async def persist(self) -> None:
        await self.initialize()
        async with self._lock:
            await asyncio.to_thread(self._persist_index_sync)
            await self.serializer.save(id_to_row=self.id_to_row, row_to_id=self.row_to_id, vectors=self.vectors)
            log_event("rag_faiss_index_persisted", index_name=self.config.index_name, vector_count=len(self.vectors), index_path=self.config.index_path)

    def _persist_index_sync(self) -> None:
        if self._index is None:
            raise VectorPersistenceError("FAISS index is not initialized")
        try:
            faiss = import_faiss()
            ensure_index_directory(self.config.index_path)
            faiss.write_index(self._index, str(faiss_index_file(self.config.index_path, self.config.index_name)))
        except Exception as exc:
            raise VectorPersistenceError("failed to persist FAISS index", details={"index_name": self.config.index_name}) from exc

    async def rebuild(self, dense_vectors: list[DenseVector]) -> None:
        async with self._lock:
            self._index = None
            self._loaded = False
            self.id_to_row.clear()
            self.row_to_id.clear()
            self.vectors.clear()
            index_file = faiss_index_file(self.config.index_path, self.config.index_name)
            if Path(index_file).exists():
                Path(index_file).unlink()
        await self.initialize()
        await self.add_vectors(dense_vectors)
