import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, MongoClient, ReturnDocument
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError

from app.core.config import MONGO_DB_NAME, MONGO_URI

logger = logging.getLogger(__name__)

CONVERSATIONS_COLLECTION = "conversations"
SUMMARIES_COLLECTION = "summaries"
LEADS_COLLECTION = "leads"

CONVERSATION_SCHEMA_EXAMPLE: dict[str, Any] = {
    "user_id": "user-123",
    "messages": [
        {
            "role": "user",
            "content": "I need help comparing sales automation plans.",
            "timestamp": "2026-05-07T03:45:00Z",
        },
        {
            "role": "assistant",
            "content": "I can help. What is your team size?",
            "timestamp": "2026-05-07T03:45:04Z",
        },
    ],
    "summary": "User is evaluating sales automation tooling.",
    "intents": ["pricing_question", "lead_qualification"],
    "lead_status": "qualified",
    "metadata": {"channel": "chatbot"},
    "created_at": "2026-05-07T03:45:00Z",
    "updated_at": "2026-05-07T03:45:04Z",
}

SUMMARY_SCHEMA_EXAMPLE: dict[str, Any] = {
    "user_id": "user-123",
    "conversation_id": "6639f7e4e7c5a4c4e7f78012",
    "summary": "User asked about pricing and requested follow-up tomorrow.",
    "intents": ["pricing_question", "follow_up_request"],
    "created_at": "2026-05-07T03:50:00Z",
}

LEAD_SCHEMA_EXAMPLE: dict[str, Any] = {
    "user_id": "user-123",
    "lead_status": "qualified",
    "lead_data": {
        "name": "Akshat",
        "email": "akshat@example.com",
        "company": "Acme",
    },
    "intents": ["demo_request"],
    "created_at": "2026-05-07T03:55:00Z",
    "updated_at": "2026-05-07T03:55:00Z",
}

_mongo_client: MongoClient | None = None
_indexes_created = False


class MongoStoreError(RuntimeError):
    """Raised when chatbot storage cannot be read from or written to MongoDB."""


def _utc_now() -> datetime:
    """Use timezone-aware timestamps for consistent analytics queries."""
    return datetime.now(timezone.utc)


def _validate_user_id(user_id: str) -> str:
    if not user_id or not str(user_id).strip():
        raise ValueError("user_id is required")

    return str(user_id).strip()


def _get_mongo_client() -> MongoClient:
    """
    Lazily create one MongoClient per process.

    PyMongo's MongoClient is thread-safe and manages connection pooling internally,
    so reusing it avoids expensive reconnects during high-volume chatbot traffic.
    """
    global _mongo_client

    if _mongo_client is None:
        if not MONGO_URI:
            raise MongoStoreError("MONGO_URI is not configured")

        _mongo_client = MongoClient(
            MONGO_URI,
            appname="fastapi-agentic-ai-chatbot",
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=10000,
            retryWrites=True,
        )

    return _mongo_client


def _get_database() -> Database:
    return _get_mongo_client()[MONGO_DB_NAME]


def _collection(name: str) -> Collection:
    return _get_database()[name]


async def _run_blocking(func, *args, **kwargs):
    """Run blocking PyMongo work off the event loop for FastAPI async routes."""
    return await asyncio.to_thread(func, *args, **kwargs)


def _serialize_document(value: Any) -> Any:
    """Convert Mongo-specific types into API-friendly Python values."""
    if isinstance(value, ObjectId):
        return str(value)

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, list):
        return [_serialize_document(item) for item in value]

    if isinstance(value, dict):
        return {key: _serialize_document(item) for key, item in value.items()}

    return value


async def ensure_indexes() -> None:
    """Create indexes used by memory, timeline, analytics, and lead queries."""
    global _indexes_created

    if _indexes_created:
        return

    def create_indexes() -> None:
        conversations = _collection(CONVERSATIONS_COLLECTION)
        summaries = _collection(SUMMARIES_COLLECTION)
        leads = _collection(LEADS_COLLECTION)

        conversations.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
        conversations.create_index([("updated_at", DESCENDING)])
        summaries.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
        leads.create_index([("user_id", ASCENDING)], unique=True)
        leads.create_index([("lead_status", ASCENDING), ("updated_at", DESCENDING)])

    try:
        await _run_blocking(create_indexes)
    except PyMongoError as exc:
        logger.exception("Failed to create MongoDB indexes")
        raise MongoStoreError("failed to create MongoDB indexes") from exc

    _indexes_created = True


async def save_chat(
    user_id: str | dict[str, Any],
    messages: list[dict[str, Any]] | None = None,
    intents: list[str] | None = None,
    lead_status: str | None = None,
    summary: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Store one conversation log for a user.

    `user_id` may be a full document dict for backward compatibility with older
    calls, but new code should pass named arguments for clearer agent workflows.
    """
    await ensure_indexes()

    now = _utc_now()
    if isinstance(user_id, dict):
        document = {**user_id}
        document["user_id"] = _validate_user_id(document.get("user_id", ""))
        document.setdefault("messages", [])
        document.setdefault("intents", [])
        document.setdefault("lead_status", None)
        document.setdefault("summary", None)
        document.setdefault("metadata", {})
        document.setdefault("created_at", now)
        document["updated_at"] = now
    else:
        document = {
            "user_id": _validate_user_id(user_id),
            "messages": messages or [],
            "summary": summary,
            "intents": intents or [],
            "lead_status": lead_status,
            "metadata": metadata or {},
            "created_at": now,
            "updated_at": now,
        }

    try:
        result = await _run_blocking(
            _collection(CONVERSATIONS_COLLECTION).insert_one,
            document,
        )
    except PyMongoError as exc:
        logger.exception("Failed to save chat for user_id=%s", document.get("user_id"))
        raise MongoStoreError("failed to save chat") from exc

    document["_id"] = result.inserted_id
    return _serialize_document(document)


async def get_chat_history(user_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """Return recent conversation logs for a user, newest first."""
    await ensure_indexes()
    user_id = _validate_user_id(user_id)
    limit = max(1, min(limit, 200))

    def fetch_history() -> list[dict[str, Any]]:
        cursor = (
            _collection(CONVERSATIONS_COLLECTION)
            .find({"user_id": user_id})
            .sort("created_at", DESCENDING)
            .limit(limit)
        )
        return list(cursor)

    try:
        history = await _run_blocking(fetch_history)
    except PyMongoError as exc:
        logger.exception("Failed to get chat history for user_id=%s", user_id)
        raise MongoStoreError("failed to get chat history") from exc

    return [_serialize_document(document) for document in history]


async def save_summary(
    user_id: str,
    summary: str,
    conversation_id: str | None = None,
    intents: list[str] | None = None,
) -> dict[str, Any]:
    """Store an AI-generated conversation summary for memory and analytics."""
    await ensure_indexes()
    user_id = _validate_user_id(user_id)
    now = _utc_now()
    document = {
        "user_id": user_id,
        "conversation_id": conversation_id,
        "summary": summary,
        "intents": intents or [],
        "created_at": now,
    }

    try:
        result = await _run_blocking(_collection(SUMMARIES_COLLECTION).insert_one, document)
    except PyMongoError as exc:
        logger.exception("Failed to save summary for user_id=%s", user_id)
        raise MongoStoreError("failed to save summary") from exc

    document["_id"] = result.inserted_id
    return _serialize_document(document)


async def save_lead(
    user_id: str,
    lead_status: str,
    lead_data: dict[str, Any] | None = None,
    intents: list[str] | None = None,
) -> dict[str, Any]:
    """
    Upsert lead tracking data for a chatbot user.

    One lead profile is kept per user so qualification and follow-up state can be
    updated over multiple conversations.
    """
    await ensure_indexes()
    user_id = _validate_user_id(user_id)
    now = _utc_now()
    update = {
        "$set": {
            "lead_status": lead_status,
            "lead_data": lead_data or {},
            "intents": intents or [],
            "updated_at": now,
        },
        "$setOnInsert": {
            "user_id": user_id,
            "created_at": now,
        },
    }

    def upsert_lead() -> dict[str, Any] | None:
        return _collection(LEADS_COLLECTION).find_one_and_update(
            {"user_id": user_id},
            update,
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

    try:
        document = await _run_blocking(upsert_lead)
    except PyMongoError as exc:
        logger.exception("Failed to save lead for user_id=%s", user_id)
        raise MongoStoreError("failed to save lead") from exc

    return _serialize_document(document or {})


async def close_mongo_client() -> None:
    """Close the shared MongoClient during application shutdown or tests."""
    global _indexes_created, _mongo_client

    if _mongo_client is not None:
        _mongo_client.close()
        _mongo_client = None
        _indexes_created = False
