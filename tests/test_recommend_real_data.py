"""L4 — slider→first-card alignment on the REAL cravings.db catalog.

The synthetic pools in test_recommend_alignment.py are uniform; production is heavily
mild-skewed (spice median ~0.10, only ~16% of dishes >= 0.6). This test runs the actual
guest candidate-selection code (db.get_popular_food_items via build_guest_intake) against
the live DB, then scores with a freshly-seeded model — answering "does a spicy guest get
pulled to the spicy end of whatever the real catalog offered?"

Read-only: opens cravings.db with no writes. Skips cleanly if the DB is absent (CI).
"""

import asyncio
import sqlite3
from pathlib import Path

import numpy as np
import pytest

import db
from swipe.intake import build_guest_intake
from swipe.session import SessionStore
from model.thompson import ThompsonSamplingModel

REAL_DB = Path(__file__).resolve().parent.parent / "cravings.db"

# Per-session candidate pool is a random ~50-dish draw; run many fresh sessions.
N_SESSIONS = 200
# The bug, stated directly: a spicy guest should almost never get a MILD first card.
MILD_CUTOFF = 0.20            # spice < 0.20 == "mild" (catalog median is ~0.10)
MAX_MILD_MISS = 0.06          # allow ≤6% (residual exploration / genuinely mild pools)
MIN_MEAN_TOP_SPICE = 0.55     # mean top-1 spice must dwarf catalog mean (~0.24)


def _real_db_available() -> bool:
    if not REAL_DB.exists():
        return False
    conn = sqlite3.connect(REAL_DB)
    try:
        n = conn.execute(
            "SELECT COUNT(*) FROM food_items WHERE tagging_status='tagged'"
        ).fetchone()[0]
        return n >= 100
    except sqlite3.Error:
        return False
    finally:
        conn.close()


pytestmark = pytest.mark.skipif(
    not _real_db_available(), reason="real cravings.db not present or too small"
)


def _draw_pool(conn, sessions, session_id, top_n=1):
    """Real guest candidate pool + context for one fresh session."""
    snap, candidates = asyncio.run(
        build_guest_intake(
            conn, sessions, session_id,
            dietary_restrictions=[], safety_overrides=[],
            dietary_mode="standard", mood="no_preference", hour=12.0,
            top_n=top_n, extra_excluded=None,
        )
    )
    return snap, candidates


def _seeded_top1_spice(taste_prefs, conn, sessions, session_id):
    snap, candidates = _draw_pool(conn, sessions, session_id)
    pool_spice = np.array([float(c.get("spice_level") or 0.0) for c in candidates])
    model = ThompsonSamplingModel()
    if taste_prefs:
        model.set_prior_from_onboarding(taste_prefs)
    top_idx = model.score_items(candidates, snap.to_context())[0][0]
    return float(candidates[top_idx].get("spice_level") or 0.0), pool_spice


def test_spicy_slider_avoids_mild_food_on_real_catalog():
    """A maxed spice slider almost never yields a MILD first card across fresh guest
    sessions on the real mild-skewed catalog, and mean top-1 spice dwarfs the catalog
    mean. This is the regression test bound to the reported bug ("I asked for spicy and
    got mild/sweet food")."""
    conn = sqlite3.connect(REAL_DB)
    conn.row_factory = sqlite3.Row
    sessions = SessionStore()
    try:
        top_vals = []
        for i in range(N_SESSIONS):
            top_spice, _ = _seeded_top1_spice(
                {"spice_level": 1.0}, conn, sessions, f"real_spicy_{i}"
            )
            top_vals.append(top_spice)
    finally:
        conn.close()

    top = np.array(top_vals)
    mild_miss = float((top < MILD_CUTOFF).mean())
    mean_top = float(top.mean())

    assert mild_miss <= MAX_MILD_MISS, (
        f"Spicy guest got a MILD first card in {mild_miss:.0%} of sessions "
        f"(allow <={MAX_MILD_MISS:.0%}). mean top-1 spice={mean_top:.2f}"
    )
    assert mean_top >= MIN_MEAN_TOP_SPICE, (
        f"mean top-1 spice {mean_top:.2f} too low (need >={MIN_MEAN_TOP_SPICE}); "
        f"catalog mean is ~0.24."
    )


def test_neutral_slider_no_tail_bias_on_real_catalog():
    """No slider ⇒ top-1 spice tracks the catalog (low), not the spicy tail. Confirms the
    fix doesn't smuggle in a global high-attribute bias on real data."""
    conn = sqlite3.connect(REAL_DB)
    conn.row_factory = sqlite3.Row
    sessions = SessionStore()
    try:
        top_vals = []
        for i in range(N_SESSIONS):
            top_spice, _ = _seeded_top1_spice({}, conn, sessions, f"real_neutral_{i}")
            top_vals.append(top_spice)
        mean_top = float(np.mean(top_vals))
    finally:
        conn.close()

    # Neutral top-1 should sit near the mild catalog mean, well below the seeded case.
    assert mean_top < 0.40, (
        f"Neutral guest mean top-1 spice {mean_top:.2f} is biased high (catalog mean ~0.24)."
    )
