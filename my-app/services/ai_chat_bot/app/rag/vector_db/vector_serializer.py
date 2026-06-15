import asyncio
import json

from pydantic import TypeAdapter

from app.rag.exceptions.vector_db_exceptions import VectorPersistenceError
from app.rag.models.vector_models import StoredVector
from app.rag.utils.faiss_helpers import ensure_index_directory, metadata_file


class VectorSerializer:
    """Persist vector metadata and FAISS row mappings beside the index file."""

    def __init__(self, *, index_path: str, index_name: str) -> None:
        self.index_path = index_path
        self.index_name = index_name
        self._stored_vector_adapter = TypeAdapter(dict[str, StoredVector])

    async def save(self, *, id_to_row: dict[str, int], row_to_id: dict[int, str], vectors: dict[str, StoredVector]) -> None:
        await asyncio.to_thread(self._save_sync, id_to_row=id_to_row, row_to_id=row_to_id, vectors=vectors)

    async def load(self) -> tuple[dict[str, int], dict[int, str], dict[str, StoredVector]]:
        return await asyncio.to_thread(self._load_sync)

    def _save_sync(self, *, id_to_row: dict[str, int], row_to_id: dict[int, str], vectors: dict[str, StoredVector]) -> None:
        try:
            ensure_index_directory(self.index_path)
            payload = {
                "id_to_row": id_to_row,
                "row_to_id": {str(key): value for key, value in row_to_id.items()},
                "vectors": {key: value.model_dump(mode="json") for key, value in vectors.items()},
            }
            metadata_file(self.index_path, self.index_name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            raise VectorPersistenceError("failed to save vector metadata", details={"index_name": self.index_name}) from exc

    def _load_sync(self) -> tuple[dict[str, int], dict[int, str], dict[str, StoredVector]]:
        path = metadata_file(self.index_path, self.index_name)
        if not path.exists():
            return {}, {}, {}

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            id_to_row = {str(key): int(value) for key, value in payload.get("id_to_row", {}).items()}
            row_to_id = {int(key): str(value) for key, value in payload.get("row_to_id", {}).items()}
            vectors = self._stored_vector_adapter.validate_python(payload.get("vectors", {}))
            return id_to_row, row_to_id, vectors
        except Exception as exc:
            raise VectorPersistenceError("failed to load vector metadata", details={"index_name": self.index_name}) from exc
