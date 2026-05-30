import asyncio
import os
import sqlite3
from datetime import UTC, datetime
from typing import Any

from app.config.settings import settings
from app.core.config import CONVERSATION_DB_PATH, OWNER_EMAIL
from app.core.logger import log_error, log_event
from app.core.performance import measure
from app.utils.ttl_cache import TTLCache


class OwnerSettingsError(RuntimeError):
    """Raised when owner email settings cannot be persisted."""


_emails_cache: TTLCache[list[dict[str, Any]]] = TTLCache(ttl_seconds=settings.owner_email_cache_ttl_seconds)
_db_initialized = False
_init_lock = asyncio.Lock()
_write_lock = asyncio.Lock()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _connect() -> sqlite3.Connection:
    db_dir = os.path.dirname(CONVERSATION_DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    connection = sqlite3.connect(CONVERSATION_DB_PATH, timeout=0.25)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout=250")
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA synchronous=NORMAL")
    return connection


async def init_owner_settings_db() -> None:
    """Create the owner_settings table used by lifecycle close notifications."""
    global _db_initialized
    if _db_initialized:
        return

    async with _init_lock:
        if _db_initialized:
            return

        def initialize() -> None:
            with _connect() as connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS owner_settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT NOT NULL UNIQUE,
                        active INTEGER NOT NULL DEFAULT 1,
                        created_at TEXT NOT NULL
                    )
                    """
                )
                connection.execute("CREATE INDEX IF NOT EXISTS idx_owner_settings_active_id ON owner_settings(active, id)")
                connection.commit()

        try:
            async with measure("db", "owner_settings.init"):
                await asyncio.to_thread(initialize)
        except sqlite3.Error as exc:
            log_error("Owner settings table initialization failed", error_type=type(exc).__name__)
            raise OwnerSettingsError("failed to initialize owner settings table") from exc
        _db_initialized = True


def _normalize_email(email: str) -> str:
    normalized = str(email or "").strip().lower()
    if not normalized or "@" not in normalized:
        raise ValueError("valid email is required")
    return normalized


async def add_owner_email(email: str, active: bool = True) -> dict[str, Any]:
    """Add or reactivate an owner email that should receive closed-chat summaries."""
    normalized = _normalize_email(email)
    await init_owner_settings_db()

    def insert_email() -> None:
        with _connect() as connection:
            connection.execute(
                """
                INSERT INTO owner_settings (email, active, created_at)
                VALUES (?, ?, ?)
                ON CONFLICT(email) DO UPDATE SET active = excluded.active
                """,
                (normalized, int(active), _utc_now()),
            )
            connection.commit()

    try:
        async with _write_lock:
            async with measure("db", "owner_settings.add"):
                await asyncio.to_thread(insert_email)
    except sqlite3.Error as exc:
        log_error("Owner email add failed", email=normalized, error_type=type(exc).__name__)
        raise OwnerSettingsError("failed to add owner email") from exc

    _emails_cache.invalidate_prefix("owner_emails:")
    log_event("owner_email_added", email=normalized, active=active)
    return {"email": normalized, "active": active}


async def update_owner_email(email: str, *, active: bool) -> dict[str, Any]:
    """Enable or disable an existing owner email."""
    normalized = _normalize_email(email)
    await init_owner_settings_db()

    def patch_email() -> int:
        with _connect() as connection:
            cursor = connection.execute(
                "UPDATE owner_settings SET active = ? WHERE email = ?",
                (int(active), normalized),
            )
            connection.commit()
            return int(cursor.rowcount)

    try:
        async with _write_lock:
            async with measure("db", "owner_settings.update"):
                rowcount = await asyncio.to_thread(patch_email)
    except sqlite3.Error as exc:
        log_error("Owner email update failed", email=normalized, error_type=type(exc).__name__)
        raise OwnerSettingsError("failed to update owner email") from exc

    if rowcount == 0:
        raise OwnerSettingsError("owner email not found")

    _emails_cache.invalidate_prefix("owner_emails:")
    log_event("owner_email_updated", email=normalized, active=active)
    return {"email": normalized, "active": active}


async def remove_owner_email(email: str) -> bool:
    """Remove an owner email completely."""
    normalized = _normalize_email(email)
    await init_owner_settings_db()

    def delete_email() -> int:
        with _connect() as connection:
            cursor = connection.execute("DELETE FROM owner_settings WHERE email = ?", (normalized,))
            connection.commit()
            return int(cursor.rowcount)

    try:
        async with _write_lock:
            async with measure("db", "owner_settings.remove"):
                rowcount = await asyncio.to_thread(delete_email)
    except sqlite3.Error as exc:
        log_error("Owner email remove failed", email=normalized, error_type=type(exc).__name__)
        raise OwnerSettingsError("failed to remove owner email") from exc

    removed = rowcount > 0
    _emails_cache.invalidate_prefix("owner_emails:")
    log_event("owner_email_removed", email=normalized, removed=removed)
    return removed


async def list_owner_emails(active_only: bool = True) -> list[dict[str, Any]]:
    """Return owner email rows from the local owner_settings table."""
    cache_key = f"owner_emails:{active_only}"
    async with measure("cache", "owner_settings.cache_get", active_only=active_only):
        cached = _emails_cache.get(cache_key)
    if cached is not None:
        return cached

    await init_owner_settings_db()

    def fetch_emails() -> list[dict[str, Any]]:
        query = "SELECT id, email, active, created_at FROM owner_settings"
        params: tuple[Any, ...] = ()
        if active_only:
            query += " WHERE active = ?"
            params = (1,)
        query += " ORDER BY id"
        with _connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    try:
        async with measure("db", "owner_settings.list", active_only=active_only):
            result = await asyncio.to_thread(fetch_emails)
    except sqlite3.Error as exc:
        log_error("Owner email list failed", error_type=type(exc).__name__)
        raise OwnerSettingsError("failed to list owner emails") from exc

    async with measure("cache", "owner_settings.cache_set", active_only=active_only):
        _emails_cache.set(cache_key, result, ttl_seconds=settings.owner_email_cache_ttl_seconds)
    return result


async def get_active_owner_emails() -> list[str]:
    """
    Merge static OWNER_EMAIL values and dynamic DB settings.

    OWNER_EMAIL may contain one address or a comma-separated list; the database
    allows runtime add/remove/update support without changing deployment config.
    """
    static_emails = [_normalize_email(item) for item in OWNER_EMAIL.split(",") if item.strip()]
    db_emails = [row["email"] for row in await list_owner_emails(active_only=True)]
    return sorted(set(static_emails + db_emails))
