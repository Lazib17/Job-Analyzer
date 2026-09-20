"""
Local SQLite database fallback when Supabase is unavailable.
"""

import json
import logging
import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _db_path() -> Path:
    if os.getenv("VERCEL"):
        return Path("/tmp/local_data.db")
    return Path(__file__).parent / "local_data.db"
ALLOWED_TABLES = frozenset({"users", "resumes", "jobs", "analysis", "search_history"})

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    google_id TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS resumes (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    file_url TEXT NOT NULL,
    extracted_text TEXT,
    uploaded_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    job_title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    description TEXT,
    salary TEXT,
    requirements TEXT,
    job_url TEXT,
    is_favorite INTEGER DEFAULT 0,
    source_platform TEXT DEFAULT 'linkedin',
    visa_sponsorship INTEGER DEFAULT 0,
    japanese_level TEXT,
    remote_option INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS analysis (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    job_id TEXT NOT NULL,
    compatibility_score INTEGER,
    missing_skills TEXT DEFAULT '[]',
    matching_skills TEXT DEFAULT '[]',
    improvement_suggestions TEXT,
    ai_reasoning TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(user_id, job_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS search_history (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    job_title TEXT NOT NULL,
    location TEXT,
    results_count INTEGER DEFAULT 0,
    searched_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_resumes_user_id ON resumes(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_user_id ON analysis(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_job_id ON analysis(job_id);
CREATE INDEX IF NOT EXISTS idx_search_history_user_id ON search_history(user_id);
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_table(table: str) -> None:
    if table not in ALLOWED_TABLES:
        raise ValueError(f"Invalid table: {table}")


def _validate_order_by(order_by: str) -> None:
    if not re.match(r"^[a-z_]+$", order_by):
        raise ValueError(f"Invalid order_by column: {order_by}")


def init_local_db() -> None:
    """Create SQLite tables if they do not exist."""
    path = _db_path()
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA)
        _migrate_google_auth(conn)
        conn.commit()
    logger.info("Local SQLite database ready at %s", path)


def _migrate_google_auth(conn: sqlite3.Connection) -> None:
    """Add google_id and allow NULL password_hash on existing databases."""
    info = conn.execute("PRAGMA table_info(users)").fetchall()
    if not info:
        return

    columns = {row[1] for row in info}
    if "google_id" not in columns:
        conn.execute("ALTER TABLE users ADD COLUMN google_id TEXT")
        columns.add("google_id")
        logger.info("Added users.google_id column")

    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id) WHERE google_id IS NOT NULL"
    )

    password_col = next((row for row in info if row[1] == "password_hash"), None)
    not_null = bool(password_col[3]) if password_col else False
    if not not_null:
        return

    conn.execute(
        """
        CREATE TABLE users_new (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            google_id TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        INSERT INTO users_new (id, name, email, password_hash, google_id, created_at)
        SELECT id, name, email, password_hash, google_id, created_at FROM users
        """
    )
    conn.execute("DROP TABLE users")
    conn.execute("ALTER TABLE users_new RENAME TO users")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id) WHERE google_id IS NOT NULL"
    )
    logger.info("Migrated users.password_hash to allow NULL")


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def _normalize_row(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    for key in ("is_favorite", "visa_sponsorship", "remote_option"):
        if key in data and data[key] is not None:
            data[key] = bool(data[key])
    for key in ("missing_skills", "matching_skills"):
        if key in data and isinstance(data[key], str):
            try:
                data[key] = json.loads(data[key])
            except json.JSONDecodeError:
                pass
    return data


def _prepare_insert(table: str, data: dict[str, Any]) -> dict[str, Any]:
    prepared = data.copy()
    if "id" not in prepared:
        prepared["id"] = str(uuid.uuid4())

    timestamp_defaults = {
        "users": "created_at",
        "resumes": "uploaded_at",
        "jobs": "created_at",
        "analysis": "created_at",
        "search_history": "searched_at",
    }
    ts_field = timestamp_defaults.get(table)
    if ts_field and ts_field not in prepared:
        prepared[ts_field] = _now_iso()

    for key in ("is_favorite", "visa_sponsorship", "remote_option"):
        if key in prepared and isinstance(prepared[key], bool):
            prepared[key] = int(prepared[key])

    for key in ("missing_skills", "matching_skills"):
        if key in prepared and not isinstance(prepared[key], str):
            prepared[key] = json.dumps(prepared[key], ensure_ascii=False)

    return prepared


def local_fetch_one(table: str, filters: dict[str, Any]) -> Optional[dict]:
    _validate_table(table)
    clauses = [f"{key} = ?" for key in filters]
    params = list(filters.values())
    sql = f"SELECT * FROM {table} WHERE {' AND '.join(clauses)} LIMIT 1"

    with _get_connection() as conn:
        row = conn.execute(sql, params).fetchone()
    return _normalize_row(row) if row else None


def local_fetch_all(
    table: str,
    filters: Optional[dict[str, Any]] = None,
    order_by: Optional[str] = None,
    ascending: bool = False,
) -> list[dict]:
    _validate_table(table)
    sql = f"SELECT * FROM {table}"
    params: list[Any] = []

    if filters:
        clauses = [f"{key} = ?" for key in filters]
        params = list(filters.values())
        sql += f" WHERE {' AND '.join(clauses)}"

    if order_by:
        _validate_order_by(order_by)
        sql += f" ORDER BY {order_by} {'ASC' if ascending else 'DESC'}"

    with _get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_normalize_row(row) for row in rows]


def local_insert_row(table: str, data: dict[str, Any]) -> dict:
    _validate_table(table)
    prepared = _prepare_insert(table, data)
    columns = ", ".join(prepared.keys())
    placeholders = ", ".join("?" for _ in prepared)
    sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

    with _get_connection() as conn:
        conn.execute(sql, list(prepared.values()))
        conn.commit()

    return local_fetch_one(table, {"id": prepared["id"]}) or prepared


def local_update_row(table: str, row_id: str, data: dict[str, Any]) -> dict:
    _validate_table(table)
    prepared = data.copy()

    for key in ("is_favorite", "visa_sponsorship", "remote_option"):
        if key in prepared and isinstance(prepared[key], bool):
            prepared[key] = int(prepared[key])

    for key in ("missing_skills", "matching_skills"):
        if key in prepared and not isinstance(prepared[key], str):
            prepared[key] = json.dumps(prepared[key], ensure_ascii=False)

    assignments = ", ".join(f"{key} = ?" for key in prepared)
    sql = f"UPDATE {table} SET {assignments} WHERE id = ?"
    params = list(prepared.values()) + [row_id]

    with _get_connection() as conn:
        conn.execute(sql, params)
        conn.commit()

    return local_fetch_one(table, {"id": row_id}) or {}


def local_delete_row(table: str, row_id: str) -> None:
    _validate_table(table)
    with _get_connection() as conn:
        conn.execute(f"DELETE FROM {table} WHERE id = ?", (row_id,))
        conn.commit()
