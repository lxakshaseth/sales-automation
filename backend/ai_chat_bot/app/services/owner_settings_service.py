import os
import sqlite3
from datetime import datetime, timezone
from typing import Any

from app.core.config import CONVERSATION_DB_PATH, OWNER_EMAIL
from app.core.logger import log_error, log_event


class OwnerSettingsError(RuntimeError):
    """Raised when owner email settings cannot be persisted."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect() -> sqlite3.Connection:
    db_dir = os.path.dirname(CONVERSATION_DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    connection = sqlite3.connect(CONVERSATION_DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


async def init_owner_settings_db() -> None:
    """Create the owner_settings table used by lifecycle close notifications."""
    try:
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
            connection.commit()
    except sqlite3.Error as exc:
        log_error("Owner settings table initialization failed", error_type=type(exc).__name__)
        raise OwnerSettingsError("failed to initialize owner settings table") from exc


def _normalize_email(email: str) -> str:
    normalized = str(email or "").strip().lower()
    if not normalized or "@" not in normalized:
        raise ValueError("valid email is required")
    return normalized


async def add_owner_email(email: str, active: bool = True) -> dict[str, Any]:
    """Add or reactivate an owner email that should receive closed-chat summaries."""
    normalized = _normalize_email(email)
    await init_owner_settings_db()
    try:
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
    except sqlite3.Error as exc:
        log_error("Owner email add failed", email=normalized, error_type=type(exc).__name__)
        raise OwnerSettingsError("failed to add owner email") from exc

    log_event("owner_email_added", email=normalized, active=active)
    return {"email": normalized, "active": active}


async def update_owner_email(email: str, *, active: bool) -> dict[str, Any]:
    """Enable or disable an existing owner email."""
    normalized = _normalize_email(email)
    await init_owner_settings_db()
    try:
        with _connect() as connection:
            cursor = connection.execute(
                "UPDATE owner_settings SET active = ? WHERE email = ?",
                (int(active), normalized),
            )
            connection.commit()
    except sqlite3.Error as exc:
        log_error("Owner email update failed", email=normalized, error_type=type(exc).__name__)
        raise OwnerSettingsError("failed to update owner email") from exc

    if cursor.rowcount == 0:
        raise OwnerSettingsError("owner email not found")

    log_event("owner_email_updated", email=normalized, active=active)
    return {"email": normalized, "active": active}


async def remove_owner_email(email: str) -> bool:
    """Remove an owner email completely."""
    normalized = _normalize_email(email)
    await init_owner_settings_db()
    try:
        with _connect() as connection:
            cursor = connection.execute("DELETE FROM owner_settings WHERE email = ?", (normalized,))
            connection.commit()
    except sqlite3.Error as exc:
        log_error("Owner email remove failed", email=normalized, error_type=type(exc).__name__)
        raise OwnerSettingsError("failed to remove owner email") from exc

    removed = cursor.rowcount > 0
    log_event("owner_email_removed", email=normalized, removed=removed)
    return removed


async def list_owner_emails(active_only: bool = True) -> list[dict[str, Any]]:
    """Return owner email rows from the local owner_settings table."""
    await init_owner_settings_db()
    query = "SELECT id, email, active, created_at FROM owner_settings"
    params: tuple[Any, ...] = ()
    if active_only:
        query += " WHERE active = ?"
        params = (1,)
    query += " ORDER BY id"

    try:
        with _connect() as connection:
            rows = connection.execute(query, params).fetchall()
    except sqlite3.Error as exc:
        log_error("Owner email list failed", error_type=type(exc).__name__)
        raise OwnerSettingsError("failed to list owner emails") from exc

    return [dict(row) for row in rows]


async def get_active_owner_emails() -> list[str]:
    """
    Merge static OWNER_EMAIL values and dynamic DB settings.

    OWNER_EMAIL may contain one address or a comma-separated list; the database
    allows runtime add/remove/update support without changing deployment config.
    """
    static_emails = [_normalize_email(item) for item in OWNER_EMAIL.split(",") if item.strip()]
    db_emails = [row["email"] for row in await list_owner_emails(active_only=True)]
    return sorted(set(static_emails + db_emails))
