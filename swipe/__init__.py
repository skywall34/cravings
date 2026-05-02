"""Swipe lifecycle module.

Owns the contract between Right-Swipe / Left-Swipe and the rest of the app:
context capture at recommend time, tamper-proof round-trip via signed token,
denormalized DB write, model update, session seen-set update.

Public surface:
    Snapshot          — frozen context captured at recommend time
    SessionStore      — per-session seen-set
    capture()         — build a Snapshot from current user state
    seal()/verify()   — sign/verify the snapshot for client round-trip
    record_swipe()    — full Right-Swipe / Left-Swipe lifecycle
"""

from swipe.snapshot import Snapshot, capture, seal, verify, SnapshotError
from swipe.session import SessionStore
from swipe.recorder import record_swipe

__all__ = [
    "Snapshot",
    "SessionStore",
    "capture",
    "seal",
    "verify",
    "record_swipe",
    "SnapshotError",
]
