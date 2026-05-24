"""Swipe lifecycle module.

Owns the full contract of a Swipe Session:
  snapshot.py    — context capture at recommend time; HMAC-signed token for round-trip
  session.py     — in-memory seen-set scoped per session_id
  recorder.py    — Right-Swipe / Left-Swipe lifecycle (model + DB + session)
  intake.py      — candidate filtering, response shaping, image URL construction
"""

from swipe.snapshot import Snapshot, capture, seal, verify, SnapshotError
from swipe.session import SessionStore
from swipe.recorder import record_swipe
from swipe.intake import build_intake, shape_results, add_image_urls

__all__ = [
    "Snapshot",
    "SessionStore",
    "capture",
    "seal",
    "verify",
    "record_swipe",
    "SnapshotError",
    "build_intake",
    "shape_results",
    "add_image_urls",
]
