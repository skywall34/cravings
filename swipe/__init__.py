"""Swipe lifecycle module.

Owns the full contract of a Swipe Session:
  snapshot.py    — context capture at recommend time; HMAC-signed token for round-trip
  session.py     — in-memory seen-set scoped per session_id
  recorder.py    — Right-Swipe / Left-Swipe lifecycle (model + DB + session)
  intake.py      — candidate filtering, response shaping, image URL construction
"""

from swipe.snapshot import Snapshot, capture, capture_guest, seal, verify, verify_guest, check_item, SnapshotError
from swipe.session import SessionStore
from swipe.recorder import record_swipe, reward_for_direction, SwipeError
from swipe.intake import build_intake, build_guest_intake, shape_results, add_image_urls

__all__ = [
    "Snapshot",
    "SessionStore",
    "capture",
    "capture_guest",
    "seal",
    "verify",
    "verify_guest",
    "check_item",
    "record_swipe",
    "reward_for_direction",
    "SwipeError",
    "SnapshotError",
    "build_intake",
    "build_guest_intake",
    "shape_results",
    "add_image_urls",
]
