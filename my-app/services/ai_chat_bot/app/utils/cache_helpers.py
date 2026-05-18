import hashlib
import json
from typing import Any


def stable_json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def build_cache_hash(value: Any) -> str:
    payload = stable_json_dumps(value)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_cache_key(namespace: str, value: Any, *, version: str = "v1") -> str:
    return f"opt:{version}:{namespace}:{build_cache_hash(value)}"


def normalize_query_for_cache(query: str) -> str:
    return " ".join(str(query or "").casefold().split())

