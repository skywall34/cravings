"""User CRUD, authentication, and recent-likes management."""

import hashlib
import hmac
import json
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

import bcrypt as _bcrypt


def generate_api_token() -> str:
    return secrets.token_urlsafe(24)


def insert_user(
    conn: sqlite3.Connection,
    name: str,
    dietary_flags_bitmask: int = 0,
    safety_overrides_bitmask: int = 0,
) -> tuple[int, str]:
    token = generate_api_token()
    cursor = conn.execute(
        "INSERT INTO users (name, api_token, dietary_flags_bitmask, safety_overrides_bitmask) "
        "VALUES (?, ?, ?, ?)",
        [name, token, dietary_flags_bitmask, safety_overrides_bitmask],
    )
    conn.commit()
    return cursor.lastrowid, token


def get_user_by_token(conn: sqlite3.Connection, token: str) -> dict | None:
    row = conn.execute("SELECT * FROM users WHERE api_token = ?", [token]).fetchone()
    return dict(row) if row else None


def get_user(conn: sqlite3.Connection, user_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM users WHERE id = ?", [user_id]).fetchone()
    return dict(row) if row else None


def update_user_model_state(
    conn: sqlite3.Connection,
    user_id: int,
    mu_blob: bytes,
    b_blob: bytes,
    total_swipes: int,
    last_decay_ts: float,
    drift_active: bool,
) -> None:
    conn.execute(
        "UPDATE users SET mu_blob = ?, b_blob = ?, total_swipes = ?, "
        "last_decay_ts = ?, drift_active = ?, updated_at = CURRENT_TIMESTAMP "
        "WHERE id = ?",
        [mu_blob, b_blob, total_swipes, last_decay_ts, int(drift_active), user_id],
    )
    conn.commit()


def update_user_dietary(
    conn: sqlite3.Connection,
    user_id: int,
    dietary_flags_bitmask: int,
    safety_overrides_bitmask: int,
) -> None:
    conn.execute(
        "UPDATE users SET dietary_flags_bitmask = ?, safety_overrides_bitmask = ?, "
        "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        [dietary_flags_bitmask, safety_overrides_bitmask, user_id],
    )
    conn.commit()


def update_user_onboarding(
    conn: sqlite3.Connection,
    user_id: int,
    dietary_flags_bitmask: int,
    safety_overrides_bitmask: int,
) -> None:
    conn.execute(
        "UPDATE users SET dietary_flags_bitmask = ?, safety_overrides_bitmask = ?, "
        "onboarding_complete = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        [dietary_flags_bitmask, safety_overrides_bitmask, user_id],
    )
    conn.commit()


def mark_onboarding_complete(conn: sqlite3.Connection, user_id: int) -> None:
    conn.execute(
        "UPDATE users SET onboarding_complete = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        [user_id],
    )
    conn.commit()


def get_user_by_email(conn: sqlite3.Connection, email: str) -> dict | None:
    row = conn.execute("SELECT * FROM users WHERE email = ?", [email.lower()]).fetchone()
    return dict(row) if row else None


def attach_credentials(
    conn: sqlite3.Connection, user_id: int, email: str, password_hash: str
) -> None:
    conn.execute(
        "UPDATE users SET email = ?, password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        [email.lower(), password_hash, user_id],
    )
    conn.commit()


def create_registered_user(
    conn: sqlite3.Connection, email: str, password_hash: str, name: str
) -> tuple[int, str]:
    token = generate_api_token()
    cursor = conn.execute(
        "INSERT INTO users (name, api_token, email, password_hash) VALUES (?, ?, ?, ?)",
        [name, token, email.lower(), password_hash],
    )
    conn.commit()
    return cursor.lastrowid, token


def rotate_api_token(conn: sqlite3.Connection, user_id: int) -> str:
    new_token = generate_api_token()
    conn.execute(
        "UPDATE users SET api_token = ?, token_issued_at = CURRENT_TIMESTAMP, "
        "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        [new_token, user_id],
    )
    conn.commit()
    return new_token


def update_password(conn: sqlite3.Connection, user_id: int, password_hash: str) -> str:
    new_token = generate_api_token()
    conn.execute(
        "UPDATE users SET password_hash = ?, password_changed_at = CURRENT_TIMESTAMP, "
        "api_token = ?, token_issued_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP "
        "WHERE id = ?",
        [password_hash, new_token, user_id],
    )
    conn.commit()
    return new_token


def hash_password(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode(), _bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode(), hashed.encode())


# ---------------------------------------------------------------------------
# Email verification (one-time 6-digit codes)
#
# Codes are short-lived and low-entropy, so bcrypt (slow, per-attempt) is the
# wrong tool — a sha256 hash plus a constant-time compare is sufficient and we
# never persist the plaintext. Login is gated on users.email_verified.
# ---------------------------------------------------------------------------

VERIFICATION_TTL_MINUTES = 10
VERIFICATION_RESEND_COOLDOWN_SECONDS = 30
VERIFICATION_MAX_ATTEMPTS = 5


def generate_verification_code() -> str:
    """Return a zero-padded 6-digit numeric code."""
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_verification_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def set_email_verified(conn: sqlite3.Connection, user_id: int) -> None:
    conn.execute(
        "UPDATE users SET email_verified = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        [user_id],
    )
    conn.commit()


def upsert_verification(conn: sqlite3.Connection, email: str, code: str) -> None:
    """Store (or replace) the active code for an email, resetting attempts."""
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=VERIFICATION_TTL_MINUTES)
    conn.execute(
        "INSERT INTO email_verifications (email, code_hash, expires_at, attempts, last_sent_at) "
        "VALUES (?, ?, ?, 0, CURRENT_TIMESTAMP) "
        "ON CONFLICT(email) DO UPDATE SET "
        "  code_hash = excluded.code_hash, expires_at = excluded.expires_at, "
        "  attempts = 0, last_sent_at = CURRENT_TIMESTAMP",
        [email.lower(), hash_verification_code(code), expires_at.isoformat()],
    )
    conn.commit()


def get_verification(conn: sqlite3.Connection, email: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM email_verifications WHERE email = ?", [email.lower()]
    ).fetchone()
    return dict(row) if row else None


def bump_verification_attempts(conn: sqlite3.Connection, email: str) -> int:
    """Increment the failed-attempt counter and return the new value.

    Guarded by `WHERE attempts < MAX` so the read-check-increment is one
    atomic statement — concurrent mismatched-code requests can't all read
    the same pre-increment count and slip past the cap before any of their
    increments land (SQLite serializes the UPDATEs).
    """
    row = conn.execute(
        "UPDATE email_verifications SET attempts = attempts + 1 "
        "WHERE email = ? AND attempts < ? RETURNING attempts",
        [email.lower(), VERIFICATION_MAX_ATTEMPTS],
    ).fetchone()
    conn.commit()
    if row is not None:
        return row["attempts"]
    row = conn.execute(
        "SELECT attempts FROM email_verifications WHERE email = ?", [email.lower()]
    ).fetchone()
    return row["attempts"] if row else VERIFICATION_MAX_ATTEMPTS


def delete_verification(conn: sqlite3.Connection, email: str) -> None:
    conn.execute("DELETE FROM email_verifications WHERE email = ?", [email.lower()])
    conn.commit()


def verification_is_expired(row: dict) -> bool:
    expires = datetime.fromisoformat(row["expires_at"])
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) >= expires


def verification_resend_too_soon(row: dict) -> int:
    """Seconds remaining on the resend cooldown, or 0 if a resend is allowed."""
    sent = datetime.fromisoformat(row["last_sent_at"])
    if sent.tzinfo is None:
        sent = sent.replace(tzinfo=timezone.utc)
    elapsed = (datetime.now(timezone.utc) - sent).total_seconds()
    remaining = VERIFICATION_RESEND_COOLDOWN_SECONDS - elapsed
    return max(0, int(remaining + 0.999)) if remaining > 0 else 0


def verification_code_matches(row: dict, code: str) -> bool:
    return hmac.compare_digest(row["code_hash"], hash_verification_code(code))


def get_recent_likes(conn: sqlite3.Connection, user_id: int) -> list[int]:
    row = conn.execute(
        "SELECT recent_likes_json FROM users WHERE id = ?", [user_id]
    ).fetchone()
    if row is None or not row["recent_likes_json"]:
        return []
    return json.loads(row["recent_likes_json"])


def push_recent_like(
    conn: sqlite3.Connection, user_id: int, item_id: int, max_len: int = 10
) -> None:
    likes = get_recent_likes(conn, user_id)
    if item_id in likes:
        likes.remove(item_id)
    likes.append(item_id)
    if len(likes) > max_len:
        likes = likes[-max_len:]
    conn.execute(
        "UPDATE users SET recent_likes_json = ? WHERE id = ?",
        [json.dumps(likes), user_id],
    )
    conn.commit()


def delete_user(conn: sqlite3.Connection, user_id: int) -> None:
    conn.execute("DELETE FROM users WHERE id = ?", [user_id])


def set_premium(conn: sqlite3.Connection, user_id: int) -> None:
    conn.execute(
        "UPDATE users SET is_premium = 1, premium_since = CURRENT_TIMESTAMP, "
        "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        [user_id],
    )
    conn.commit()


def create_billing_session(
    conn: sqlite3.Connection, session_id: str, user_id: int, amount_cents: int
) -> None:
    conn.execute(
        "INSERT INTO billing_sessions (session_id, user_id, amount_cents) VALUES (?, ?, ?)",
        [session_id, user_id, amount_cents],
    )
    conn.commit()


def get_billing_session(conn: sqlite3.Connection, session_id: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM billing_sessions WHERE session_id = ?", [session_id]
    ).fetchone()
    return dict(row) if row else None


def complete_billing_session(conn: sqlite3.Connection, session_id: str) -> None:
    conn.execute(
        "UPDATE billing_sessions SET status = 'completed', completed_at = CURRENT_TIMESTAMP "
        "WHERE session_id = ?",
        [session_id],
    )
    conn.commit()
