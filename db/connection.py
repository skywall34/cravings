"""SQLite connection management, schema init, and migration."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

SCHEMA_PATH = Path(__file__).parent / "schema.sql"
DEFAULT_DB_PATH = Path(__file__).parent.parent / "cravings.db"


def get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_connection(db_path: Path = DEFAULT_DB_PATH) -> Generator[sqlite3.Connection, None, None]:
    conn = get_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()


def init_db(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = get_connection(db_path)
    schema_sql = SCHEMA_PATH.read_text()
    conn.executescript(schema_sql)
    _migrate(conn)
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    """Idempotent column adds for existing databases."""
    swipe_cols = {r["name"] for r in conn.execute("PRAGMA table_info(swipe_events)").fetchall()}
    if "recent_rejection_rate" not in swipe_cols:
        conn.execute("ALTER TABLE swipe_events ADD COLUMN recent_rejection_rate REAL NOT NULL DEFAULT 0.0")
    if "days_since_last_session" not in swipe_cols:
        conn.execute("ALTER TABLE swipe_events ADD COLUMN days_since_last_session REAL NOT NULL DEFAULT 0.0")

    user_cols = {r["name"] for r in conn.execute("PRAGMA table_info(users)").fetchall()}
    if "email" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN email TEXT")
    if "password_hash" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
    if "password_changed_at" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN password_changed_at TIMESTAMP")
    if "token_issued_at" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN token_issued_at TIMESTAMP")
        conn.execute("UPDATE users SET token_issued_at = CURRENT_TIMESTAMP WHERE token_issued_at IS NULL")

    food_cols = {r["name"] for r in conn.execute("PRAGMA table_info(food_items)").fetchall()}
    if "embedding" not in food_cols:
        conn.execute("ALTER TABLE food_items ADD COLUMN embedding BLOB")
    if "image_slug" not in food_cols:
        conn.execute("ALTER TABLE food_items ADD COLUMN image_slug TEXT")
    if "image_hash" not in food_cols:
        conn.execute("ALTER TABLE food_items ADD COLUMN image_hash TEXT")
    if "image_author" not in food_cols:
        conn.execute("ALTER TABLE food_items ADD COLUMN image_author TEXT")
    if "image_license" not in food_cols:
        conn.execute("ALTER TABLE food_items ADD COLUMN image_license TEXT")
    if "image_source_url" not in food_cols:
        conn.execute("ALTER TABLE food_items ADD COLUMN image_source_url TEXT")
    if "image_review_status" not in food_cols:
        conn.execute("ALTER TABLE food_items ADD COLUMN image_review_status TEXT NOT NULL DEFAULT 'auto'")
    if "image_judge_verdict" not in food_cols:
        conn.execute("ALTER TABLE food_items ADD COLUMN image_judge_verdict TEXT")
    if "image_judge_reason" not in food_cols:
        conn.execute("ALTER TABLE food_items ADD COLUMN image_judge_reason TEXT")

    if "recent_likes_json" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN recent_likes_json TEXT")
    if "is_premium" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN is_premium INTEGER NOT NULL DEFAULT 0")
    if "premium_since" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN premium_since TIMESTAMP")

    conn.execute(
        "CREATE TABLE IF NOT EXISTS billing_sessions ("
        "  session_id TEXT PRIMARY KEY,"
        "  user_id INTEGER NOT NULL REFERENCES users(id),"
        "  status TEXT NOT NULL DEFAULT 'pending',"
        "  amount_cents INTEGER NOT NULL,"
        "  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,"
        "  completed_at TIMESTAMP"
        ")"
    )

    conn.execute(
        "CREATE TABLE IF NOT EXISTS user_item_impressions ("
        "  user_id INTEGER NOT NULL REFERENCES users(id),"
        "  food_item_id INTEGER NOT NULL REFERENCES food_items(id),"
        "  count INTEGER NOT NULL DEFAULT 0,"
        "  last_seen TIMESTAMP,"
        "  PRIMARY KEY (user_id, food_item_id)"
        ")"
    )

    try:
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE email IS NOT NULL"
        )
    except sqlite3.OperationalError:
        pass

    conn.commit()
