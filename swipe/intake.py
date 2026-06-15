"""Recommendation intake: snapshot capture + candidate filtering for a Swipe Session."""

from __future__ import annotations

import sqlite3

import db.database as db
from swipe.session import SessionStore
from swipe.snapshot import Snapshot, capture, capture_guest, seal
from tagging.safety import UserFilter, compute_safety_bitmask


async def build_intake(
    conn: sqlite3.Connection,
    sessions: SessionStore,
    user: dict,
    hour: float | None,
    session_id: str,
) -> tuple[Snapshot, list[dict]]:
    """Capture context snapshot and eligible candidates for the Swipe Session.

    Returns (snapshot, candidates). Raises nothing — callers check empty candidates.
    """
    snapshot = capture(conn, user["id"], hour)
    filt = UserFilter.from_user(user)
    excluded = await sessions.seen(session_id)
    candidates = db.get_eligible_food_items(conn, filt.safety_mask, filt.dietary_restrictions, excluded)
    return snapshot, candidates


async def build_guest_intake(
    conn: sqlite3.Connection,
    sessions: SessionStore,
    session_id: str,
    dietary_restrictions: list[str],
    safety_overrides: list[str],
    hour: float | None,
    top_n: int,
    extra_excluded: list[int] | None = None,
) -> tuple[Snapshot, list[dict]]:
    """Popularity-ranked candidates + guest snapshot for stateless guests."""
    safety_mask = compute_safety_bitmask(safety_overrides)
    filt = UserFilter(safety_mask=safety_mask, dietary_restrictions=dietary_restrictions)
    session_excluded = await sessions.seen(session_id)
    excluded = list(set(session_excluded) | set(extra_excluded or []))
    candidates = db.get_popular_food_items(
        conn, filt.safety_mask, filt.dietary_restrictions, excluded, limit=max(50, top_n * 20)
    )
    import random
    random.shuffle(candidates)
    snap = capture_guest(session_id, hour)
    return snap, candidates


def shape_results(
    results: list[dict],
    candidates: list[dict],
    snapshot: Snapshot,
    base_path: str,
) -> list[dict]:
    """Enrich model results with candidate metadata, snapshot token, and image URLs."""
    id_to_candidate = {c["id"]: c for c in candidates}
    token = seal(snapshot)
    for r in results:
        r["snapshot_token"] = token
        c = id_to_candidate.get(r["id"], {})
        r.update({
            "description": c.get("description"),
            "cuisine_type": c.get("cuisine_type"),
            "spice_level": c.get("spice_level"),
            "sweetness": c.get("sweetness"),
            "richness": c.get("richness"),
            "sauce_heaviness": c.get("sauce_heaviness"),
            "veggie_density": c.get("veggie_density"),
            "dairy_content": c.get("dairy_content"),
            "protein_type": c.get("protein_type"),
            "image_slug": c.get("image_slug"),
            "image_hash": c.get("image_hash"),
            "image_author": c.get("image_author"),
            "image_license": c.get("image_license"),
            "image_source_url": c.get("image_source_url"),
            "image_review_status": c.get("image_review_status", "auto"),
        })
        add_image_urls(r, base_path)
    return results


def add_image_urls(item: dict, base_path: str) -> dict:
    slug = item.get("image_slug")
    hash_ = item.get("image_hash")
    status = item.get("image_review_status", "auto")
    # "rejected" deliberately absent — VLM judge set it; frontend falls back to cuisine placeholder
    if slug and hash_ and status in ("auto", "approved", "needs_review"):
        base = f"{base_path}/images/food/{slug}-{hash_}"
        item["image_url_400"] = f"{base}-400.webp"
        item["image_url_800"] = f"{base}-800.webp"
    else:
        item["image_url_400"] = None
        item["image_url_800"] = None
    return item
