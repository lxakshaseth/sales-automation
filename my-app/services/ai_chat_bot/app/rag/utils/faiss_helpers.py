import importlib
from pathlib import Path
from typing import Any

from app.rag.exceptions.vector_db_exceptions import VectorIndexError


def import_faiss() -> Any:
    try:
        return importlib.import_module("faiss")
    except Exception as exc:
        raise VectorIndexError(
            "faiss-cpu is not installed or could not be imported",
            details={"package": "faiss-cpu"},
        ) from exc


def ensure_index_directory(index_path: str | Path) -> Path:
    path = Path(index_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def faiss_index_file(index_path: str | Path, index_name: str) -> Path:
    return Path(index_path) / f"{index_name}.faiss"


def metadata_file(index_path: str | Path, index_name: str) -> Path:
    return Path(index_path) / f"{index_name}.metadata.json"
