import asyncio
from collections.abc import Callable
from datetime import datetime
from typing import Any, TypeVar

from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.core.config import MONGO_DB_NAME, MONGO_URI
from app.core.performance import measure
from app.exceptions.long_term_memory_exceptions import MongoMemoryConnectionError

T = TypeVar("T")

_mongo_memory_client: MongoClient | None = None


def get_mongo_memory_client() -> MongoClient:
    global _mongo_memory_client
    if _mongo_memory_client is None:
        if not MONGO_URI:
            raise MongoMemoryConnectionError("MONGO_URI is not configured")
        _mongo_memory_client = MongoClient(
            MONGO_URI,
            appname="ai-chatbot-long-term-memory",
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=10000,
            retryWrites=True,
        )
    return _mongo_memory_client


def get_mongo_memory_database():
    return get_mongo_memory_client()[MONGO_DB_NAME]


async def close_mongo_memory_client() -> None:
    global _mongo_memory_client
    if _mongo_memory_client is not None:
        _mongo_memory_client.close()
        _mongo_memory_client = None


async def run_mongo(func: Callable[..., T], *args, **kwargs) -> T:
    try:
        async with measure("db", "mongo_memory.operation", function=getattr(func, "__name__", "callable")):
            return await asyncio.to_thread(func, *args, **kwargs)
    except PyMongoError as exc:
        raise MongoMemoryConnectionError("mongo memory operation failed", details={"error_type": type(exc).__name__}) from exc


def serialize_mongo_document(value: Any) -> Any:
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [serialize_mongo_document(item) for item in value]
    if isinstance(value, dict):
        return {key: serialize_mongo_document(item) for key, item in value.items()}
    return value
