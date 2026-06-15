import json
from typing import Any, TypeVar

from pydantic import BaseModel, TypeAdapter

from app.exceptions.memory_exceptions import MemorySerializationError

T = TypeVar("T")


def model_to_json(model: BaseModel) -> str:
    try:
        return model.model_dump_json()
    except Exception as exc:
        raise MemorySerializationError("failed to serialize model", details={"model": type(model).__name__}) from exc


def json_to_model(raw_value: str | bytes | None, model_type: type[T]) -> T | None:
    if raw_value is None:
        return None
    try:
        if isinstance(raw_value, bytes):
            raw_value = raw_value.decode("utf-8")
        return TypeAdapter(model_type).validate_json(raw_value)
    except Exception as exc:
        raise MemorySerializationError("failed to deserialize model", details={"model": getattr(model_type, "__name__", str(model_type))}) from exc


def json_to_dict(raw_value: str | bytes | None) -> dict[str, Any]:
    if raw_value is None:
        return {}
    try:
        if isinstance(raw_value, bytes):
            raw_value = raw_value.decode("utf-8")
        parsed = json.loads(raw_value)
        return parsed if isinstance(parsed, dict) else {}
    except Exception as exc:
        raise MemorySerializationError("failed to deserialize dictionary") from exc
