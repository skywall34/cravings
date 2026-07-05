"""Right-Swipe / Left-Swipe lifecycle: model update + denormalized DB write + session mark."""

from __future__ import annotations

import asyncio
import logging
import os
import sqlite3

import db.database as db
from swipe.session import SessionStore
from swipe.snapshot import Snapshot, SnapshotError, check_item as snapshot_check_item

logger = logging.getLogger(__name__)


class SwipeError(ValueError):
    pass


def reward_for_direction(direction: str) -> float:
    """Map a swipe direction to its reward signal. Single source of truth for both
    Registered and Guest paths so the reward policy can never drift between them."""
    if direction not in ("right", "left", "never"):
        raise SwipeError("direction must be 'right', 'left', or 'never'")
    left_reward = float(os.environ.get("CRAVINGS_LEFT_SWIPE_REWARD", "0.3"))
    never_reward = float(os.environ.get("CRAVINGS_NEVER_REWARD", "0.0"))
    return 1.0 if direction == "right" else (never_reward if direction == "never" else left_reward)


async def record_swipe(
    conn: sqlite3.Connection,
    model_service,
    sessions: SessionStore,
    user: dict,
    item: dict,
    snapshot: Snapshot,
    direction: str,
    session_id: str,
) -> int:
    """Full Right-Swipe / Left-Swipe contract. Returns total_swipes after update."""
    reward = reward_for_direction(direction)
    if snapshot.user_id != user["id"]:
        raise SwipeError("snapshot user mismatch")
    # The swiped item must be one this token actually recommended (H1) — blocks
    # training μ/B on a safety-filtered or arbitrary item the client names.
    snapshot_check_item(snapshot, item["id"])
    # Single-use nonce (H1 replay): a served item can be trained on once per
    # issued token. snapshot_id is "" only for tokens issued in the ~30min
    # before this check shipped — skip for that time-boxed transition window.
    if snapshot.snapshot_id and not db.consume_snapshot_item(
        conn, snapshot.snapshot_id, item["id"], user["id"]
    ):
        raise SnapshotError("snapshot already used for this item")

    total = await asyncio.to_thread(
        model_service.record_swipe, user["id"], item, snapshot.to_context(), reward
    )
    db.record_swipe(
        conn,
        user["id"],
        item["id"],
        direction,
        snapshot.hour,
        snapshot.recent_rejection_rate,
        snapshot.days_since_last_session,
    )
    await sessions.mark(session_id, item["id"])
    return total
