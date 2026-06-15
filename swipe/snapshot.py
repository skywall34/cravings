"""Swipe context snapshot — captured at recommend, verified at swipe."""

from __future__ import annotations

import base64
import hmac
import json
import os
import sqlite3
import time
from dataclasses import asdict, dataclass
from hashlib import sha256

import db.database as db

_TTL_SECONDS = 30 * 60  # 30min — covers human swipe latency, not session duration

_SECRET = os.environ.get("CRAVINGS_SWIPE_SECRET", "").encode() or os.urandom(32)


class SnapshotError(ValueError):
    """Raised when a snapshot token is malformed, tampered, expired, or for the wrong user."""


@dataclass(frozen=True)
class Snapshot:
    user_id: int
    hour: float
    recent_rejection_rate: float
    days_since_last_session: float
    issued_at: float
    session_id: str = ""  # guest-only: bound to session instead of user_id

    def to_context(self) -> dict:
        return {
            "hour": self.hour,
            "recent_rejection_rate": self.recent_rejection_rate,
            "days_since_last_session": self.days_since_last_session,
        }


def _current_hour() -> float:
    t = time.localtime()
    return t.tm_hour + t.tm_min / 60.0


def capture(
    conn: sqlite3.Connection,
    user_id: int,
    hour: float | None = None,
) -> Snapshot:
    """Build a Snapshot from current user state. Reads recent rejection rate
    and days-since-last-session from swipe_events."""
    return Snapshot(
        user_id=user_id,
        hour=hour if hour is not None else _current_hour(),
        recent_rejection_rate=db.recent_rejection_rate(conn, user_id),
        days_since_last_session=db.days_since_last_swipe(conn, user_id),
        issued_at=time.time(),
    )


def seal(snap: Snapshot) -> str:
    """HMAC-sign and base64-encode the snapshot. Opaque to clients."""
    payload = json.dumps(asdict(snap), separators=(",", ":"), sort_keys=True).encode()
    sig = hmac.new(_SECRET, payload, sha256).digest()
    return (
        base64.urlsafe_b64encode(payload).decode().rstrip("=")
        + "."
        + base64.urlsafe_b64encode(sig).decode().rstrip("=")
    )


def _b64decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def _decode_authentic(token: str) -> Snapshot:
    """Authenticity + freshness: decode, verify HMAC signature, and check TTL.

    Returns a structurally valid, unexpired Snapshot — but does NOT check who it
    belongs to. Callers apply their own binding (user_id or session_id) on top.
    Raises SnapshotError on any failure."""
    if not token or "." not in token:
        raise SnapshotError("missing snapshot token")
    try:
        p_b64, s_b64 = token.split(".", 1)
        payload = _b64decode(p_b64)
        sig = _b64decode(s_b64)
    except Exception as e:
        raise SnapshotError(f"malformed token: {e}") from e

    expected = hmac.new(_SECRET, payload, sha256).digest()
    if not hmac.compare_digest(sig, expected):
        raise SnapshotError("invalid signature")

    try:
        data = json.loads(payload)
        snap = Snapshot(**data)
    except Exception as e:
        raise SnapshotError(f"corrupt payload: {e}") from e

    if time.time() - snap.issued_at > _TTL_SECONDS:
        raise SnapshotError("snapshot expired")
    return snap


def verify(token: str, user_id: int) -> Snapshot:
    """Authentic + bound to this Registered user. Raises SnapshotError."""
    snap = _decode_authentic(token)
    if snap.user_id != user_id:
        raise SnapshotError("snapshot user mismatch")
    return snap


def capture_guest(
    session_id: str,
    hour: float | None = None,
) -> Snapshot:
    """Build a Snapshot for a guest. No DB reads — rates default to 0.0."""
    return Snapshot(
        user_id=0,
        session_id=session_id,
        hour=hour if hour is not None else _current_hour(),
        recent_rejection_rate=0.0,
        days_since_last_session=0.0,
        issued_at=time.time(),
    )


def verify_guest(token: str, session_id: str) -> Snapshot:
    """Authentic + bound to this guest session. Raises SnapshotError."""
    snap = _decode_authentic(token)
    if snap.user_id != 0:
        raise SnapshotError("not a guest snapshot")
    if snap.session_id != session_id:
        raise SnapshotError("snapshot session mismatch")
    return snap
