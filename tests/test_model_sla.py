"""Model accuracy SLAs — the two gates of ADR-0009, asserted as CI gates.

Gate 1 (cold start, FAST, default suite): onboarding sliders + dietary filter shape a
    sensible first card, and the dietary/safety filter never leaks an ineligible item into
    the recommendations. Cheap (a few dozen recommend() calls) so it stays in `pytest tests/`.

Gate 2 (learning, SLOW, opt-in): swiping converges and the model beats a random policy.
    Heavy (trajectories x runs x DB persist), so it's @pytest.mark.slow — excluded from the
    default suite (addopts `-m 'not slow'`), run via `pytest -m slow`. Bars are set with a
    margin below the P13-observed numbers (71.3% / +12.6pp) so RNG noise can't flap the gate.

Both require the real cravings.db (candidates come from the production intake path) and
skip cleanly if it is absent, matching tests/test_recommend_real_data.py.
"""

from __future__ import annotations

import sqlite3

import numpy as np
import pytest

import db.database as db
from scripts.sla_eval import (
    REAL_DB,
    evaluate_guest,
    evaluate_registered,
    real_db_available,
)
from swipe.intake import build_guest_intake
from swipe.session import SessionStore
from tagging.safety import has_dietary_flag

pytestmark = pytest.mark.skipif(
    not real_db_available(), reason="real cravings.db not present or too small"
)


def _open_real() -> sqlite3.Connection:
    conn = sqlite3.connect(REAL_DB)
    conn.row_factory = sqlite3.Row
    return conn


# ── Gate 1: cold start + filter (FAST, default suite) ───────────────────────


def _guest_recommend_ids(conn, sessions, session_id, *, dietary, taste, top_n=5):
    """Return (top1_item, all_recommended_items) for one fresh guest recommend call."""
    from recommender import GuestRecommender
    import asyncio

    rec = GuestRecommender(
        conn=conn, sessions=sessions, base_path="", session_max_swipes=100,
        session_id=session_id, dietary_restrictions=list(dietary),
        safety_overrides=[], taste_prefs=dict(taste),
    )
    results = asyncio.run(
        rec.recommend(mood="no_preference", dietary_mode="standard", hour=12.0,
                      top_n=top_n, excluded_ids=[])
    )
    items = [db.get_food_item(conn, r["id"]) for r in results]
    return (items[0] if items else None), items


def test_filter_never_leaks_non_vegetarian():
    """Hard invariant: with a vegetarian filter active, NO recommended item across many
    fresh guest sessions may lack the vegetarian certification bit. Binary gate."""
    conn = _open_real()
    sessions = SessionStore()
    leaked = []
    try:
        for i in range(40):
            _, items = _guest_recommend_ids(
                conn, sessions, f"leak_{i}",
                dietary=["vegetarian"], taste={"spice_level": 0.5}, top_n=5,
            )
            for it in items:
                if it is None:
                    continue
                if not has_dietary_flag(it["dietary_flags_bitmask"], "vegetarian"):
                    leaked.append(it["name"])
    finally:
        conn.close()
    assert not leaked, f"vegetarian filter leaked non-veg items: {sorted(set(leaked))[:10]}"


def test_cold_start_spicy_slider_under_vegetarian_filter():
    """A spicy slider still steers the first card toward the spicy end of the *vegetarian*
    pool — sliders and filters compose. Asserted relative to the per-session veg-pool mean
    so it can't flake on the absolute spice distribution of the veg subset."""
    import asyncio

    conn = _open_real()
    sessions = SessionStore()
    top_spices, pool_means = [], []
    try:
        for i in range(60):
            sid = f"coldveg_{i}"
            top1, _ = _guest_recommend_ids(
                conn, sessions, sid,
                dietary=["vegetarian"], taste={"spice_level": 1.0}, top_n=1,
            )
            # Re-draw the same vegetarian pool to get its spice baseline.
            _, cands = asyncio.run(build_guest_intake(
                conn, sessions, f"{sid}_pool", ["vegetarian"], [],
                "standard", "no_preference", 12.0, top_n=1, extra_excluded=None,
            ))
            if top1 is None or not cands:
                continue
            assert has_dietary_flag(top1["dietary_flags_bitmask"], "vegetarian"), (
                f"spicy-veg first card is not vegetarian: {top1['name']}"
            )
            top_spices.append(float(top1.get("spice_level") or 0.0))
            pool_means.append(float(np.mean([float(c.get("spice_level") or 0.0) for c in cands])))
    finally:
        conn.close()

    mean_top = float(np.mean(top_spices))
    mean_pool = float(np.mean(pool_means))
    assert mean_top > mean_pool + 0.15, (
        f"spicy slider under vegetarian filter did not lift first-card spice enough: "
        f"top-1 mean {mean_top:.2f} vs veg-pool mean {mean_pool:.2f}"
    )


# ── Gate 2: learning SLA (SLOW, opt-in via `pytest -m slow`) ─────────────────

# Bars (ADR-0009): mean over runs, margin below P13 (last_10 71.3%, lift +12.6pp).
LAST_10_BAR = 0.60
LIFT_BAR = 0.10


@pytest.mark.slow
def test_learning_sla_guest():
    """Guest session-scoped model: swiping converges and beats random on the real catalog."""
    m = evaluate_guest(n_runs=12, n_swipes=50)
    assert m["last_10_hit_rate"] >= LAST_10_BAR, (
        f"guest last_10 hit-rate {m['last_10_hit_rate']:.1%} < {LAST_10_BAR:.0%} "
        f"(model {m['model_overall']:.1%} vs random {m['random_overall']:.1%})"
    )
    assert m["lift"] >= LIFT_BAR, (
        f"guest lift over random {m['lift']:+.1%} < +{LIFT_BAR:.0%}"
    )


@pytest.mark.slow
def test_learning_sla_registered():
    """Registered DB-backed model: same bar, exercising μ/B persist+reload each swipe.
    Proves the guest==registered parity claim in CONTEXT.md. Fewer runs (DB per swipe is
    slow); the margin below P13 absorbs the wider noise."""
    m = evaluate_registered(n_runs=6, n_swipes=50)
    assert m["last_10_hit_rate"] >= LAST_10_BAR, (
        f"registered last_10 hit-rate {m['last_10_hit_rate']:.1%} < {LAST_10_BAR:.0%} "
        f"(model {m['model_overall']:.1%} vs random {m['random_overall']:.1%})"
    )
    assert m["lift"] >= LIFT_BAR, (
        f"registered lift over random {m['lift']:+.1%} < +{LIFT_BAR:.0%}"
    )
