"""Model accuracy SLA evaluation — the two gates of ADR-0009.

Drives the **Recommender seam** (GuestRecommender / RegisteredRecommender) against a
synthetic user on the *real* `cravings.db` catalog, so the dietary/safety filter, HMAC
snapshot round-trip, and `reward_for_direction` policy are all exercised — not just the
bare model.

Two gates:

  Gate 2 (learning) — does swiping make recommendations better, and does the model beat
      a random policy? Measured as last-10 hit-rate + lift over random, against a synthetic
      user whose hidden taste defines ground truth (reused from scripts/simulate.py).

  Gate 1 (cold start) — lives mostly in tests/test_recommend_real_data.py + test_model_sla.py;
      this script focuses on the heavy learning sweep.

This module is import-safe: the heavy functions are plain callables that the
@pytest.mark.slow gate in tests/test_model_sla.py imports with trimmed run counts. Run
directly for a full sweep:

    uv run python scripts/sla_eval.py                  # guest + registered, 30 runs
    uv run python scripts/sla_eval.py --runs 10 --guest-only

A synthetic "left" flows through reward_for_direction as the production left reward (0.3),
not a raw 0 — testing the real left/right reward effect is the point of driving the seam.
The random baseline draws from the same dietary-filtered pool but picks uniformly; it does
not train a model (no model to train), so it skips record() — it is the control, not the
subject under test.
"""

from __future__ import annotations

import asyncio
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

import db.database as db
from db.database import get_user, insert_user
from model_server.model_service import UserModelStore
from model_server.recommendation_service import ModelServer
from recommender import GuestRecommender, RegisteredRecommender
from scripts.simulate import create_synthetic_user, synthetic_swipe
from swipe.intake import build_guest_intake, build_intake
from swipe.session import SessionStore

REAL_DB = Path(__file__).resolve().parent.parent / "cravings.db"

# Defaults match the P13 validation run (30 runs x 50 swipes, picky profile).
DEFAULT_RUNS = 30
DEFAULT_SWIPES = 50


def real_db_available(min_tagged: int = 100) -> bool:
    if not REAL_DB.exists():
        return False
    conn = sqlite3.connect(REAL_DB)
    try:
        n = conn.execute(
            "SELECT COUNT(*) FROM food_items WHERE tagging_status='tagged'"
        ).fetchone()[0]
        return n >= min_tagged
    except sqlite3.Error:
        return False
    finally:
        conn.close()


def _direction(hit: int) -> str:
    return "right" if hit else "left"


def _sliders_from_user(user: dict) -> dict:
    """Onboarding sliders a user with this hidden taste would plausibly set ([-1, 1])."""
    return {k: max(-1.0, min(1.0, v)) for k, v in user["preferences"].items()}


def _open_real() -> sqlite3.Connection:
    conn = sqlite3.connect(REAL_DB)
    conn.row_factory = sqlite3.Row
    return conn


# ── Gate 2: learning trajectories through the seam ──────────────────────────


async def guest_trajectory(
    conn: sqlite3.Connection,
    user: dict,
    *,
    seed: int,
    n_swipes: int,
    policy: str,
    dietary_restrictions: tuple[str, ...] = (),
) -> list[int]:
    """One guest swipe trajectory; returns the per-swipe hit list (1=right, 0=left)."""
    rng = np.random.default_rng(seed)
    sessions = SessionStore()
    sid = f"sla-guest-{policy}-{seed}"
    rec = GuestRecommender(
        conn=conn, sessions=sessions, base_path="", session_max_swipes=n_swipes + 1,
        session_id=sid, dietary_restrictions=list(dietary_restrictions),
        safety_overrides=[], taste_prefs=_sliders_from_user(user),
    )
    hits: list[int] = []
    for _ in range(n_swipes):
        if policy == "model":
            results = await rec.recommend(
                mood="no_preference", dietary_mode="standard", hour=12.0,
                top_n=1, excluded_ids=[],
            )
            if not results:
                break
            full = db.get_food_item(conn, results[0]["id"])
            hit = synthetic_swipe(user, full, rng)
            await rec.record(
                item=full, direction=_direction(hit), token=results[0]["snapshot_token"]
            )
        else:  # random control: same dietary-filtered pool, uniform pick, no learning
            _, cands = await build_guest_intake(
                conn, sessions, sid, list(dietary_restrictions), [],
                "standard", "no_preference", 12.0, top_n=1, extra_excluded=None,
            )
            if not cands:
                break
            pick = cands[int(rng.integers(len(cands)))]
            full = db.get_food_item(conn, pick["id"])
            hit = synthetic_swipe(user, full, rng)
            await sessions.mark(sid, pick["id"])
        hits.append(hit)
    return hits


async def registered_trajectory(
    db_path: Path,
    db_user: dict,
    taste_user: dict,
    model_service: ModelServer,
    *,
    seed: int,
    n_swipes: int,
    policy: str,
) -> list[int]:
    """One registered swipe trajectory against an isolated DB copy.

    db_user is the persisted users-table row (drives intake + model state); taste_user is
    the synthetic profile whose hidden weights decide each swipe (ground truth).
    """
    rng = np.random.default_rng(seed)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    sessions = SessionStore()
    sid = f"sla-reg-{policy}-{seed}"
    rec = RegisteredRecommender(conn, sessions, model_service, "", n_swipes + 1, db_user, sid)
    hits: list[int] = []
    try:
        for _ in range(n_swipes):
            if policy == "model":
                results = await rec.recommend(
                    mood="no_preference", dietary_mode="standard", hour=12.0,
                    top_n=1, excluded_ids=[],
                )
                if not results:
                    break
                full = db.get_food_item(conn, results[0]["id"])
                hit = synthetic_swipe(taste_user, full, rng)
                await rec.record(
                    item=full, direction=_direction(hit), token=results[0]["snapshot_token"]
                )
            else:
                _, cands = await build_intake(
                    conn, sessions, db_user, "standard", "no_preference", 12.0, sid
                )
                if not cands:
                    break
                pick = cands[int(rng.integers(len(cands)))]
                full = db.get_food_item(conn, pick["id"])
                hit = synthetic_swipe(taste_user, full, rng)
                await sessions.mark(sid, pick["id"])
            hits.append(hit)
    finally:
        conn.close()
    return hits


def _summarize(model_runs: list[list[int]], random_runs: list[list[int]]) -> dict:
    """Aggregate paired model/random trajectories into the SLA metrics."""
    def last10(h: list[int]) -> float:
        return float(np.mean(h[-10:])) if h else 0.0

    def overall(h: list[int]) -> float:
        return float(np.mean(h)) if h else 0.0

    last_10_mean = float(np.mean([last10(h) for h in model_runs]))
    model_overall = float(np.mean([overall(h) for h in model_runs]))
    random_overall = float(np.mean([overall(h) for h in random_runs]))
    wins = sum(overall(m) > overall(r) for m, r in zip(model_runs, random_runs))
    return {
        "runs": len(model_runs),
        "last_10_hit_rate": last_10_mean,
        "model_overall": model_overall,
        "random_overall": random_overall,
        "lift": model_overall - random_overall,
        "model_wins": wins,
    }


def evaluate_guest(
    n_runs: int = DEFAULT_RUNS,
    n_swipes: int = DEFAULT_SWIPES,
    base_seed: int = 1000,
    profile: str = "picky",
) -> dict:
    """Run the guest learning sweep on the real catalog. Returns SLA metrics."""
    conn = _open_real()
    try:
        model_runs, random_runs = [], []
        for i in range(n_runs):
            user = create_synthetic_user(seed=base_seed + i, profile=profile)
            seed = base_seed + i
            model_runs.append(
                asyncio.run(guest_trajectory(conn, user, seed=seed, n_swipes=n_swipes, policy="model"))
            )
            random_runs.append(
                asyncio.run(guest_trajectory(conn, user, seed=seed, n_swipes=n_swipes, policy="random"))
            )
    finally:
        conn.close()
    return _summarize(model_runs, random_runs)


def evaluate_registered(
    n_runs: int = DEFAULT_RUNS,
    n_swipes: int = DEFAULT_SWIPES,
    base_seed: int = 2000,
    profile: str = "picky",
) -> dict:
    """Run the registered learning sweep against an isolated copy of the real catalog."""
    tmp_dir = Path(tempfile.mkdtemp(prefix="sla_reg_"))
    db_path = tmp_dir / "cravings.db"
    shutil.copy2(REAL_DB, db_path)
    try:
        model_service = ModelServer(UserModelStore(db_path))
        model_runs, random_runs = [], []
        for i in range(n_runs):
            user_proto = create_synthetic_user(seed=base_seed + i, profile=profile)
            seed = base_seed + i
            # Fresh user (clean model) per run; seed onboarding sliders like a real signup.
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            uid, _ = insert_user(conn, f"sla_reg_{i}")
            user = get_user(conn, uid)
            conn.close()
            model_service.set_onboarding(uid, _sliders_from_user(user_proto), reset=False)

            model_runs.append(
                asyncio.run(registered_trajectory(
                    db_path, user, user_proto, model_service,
                    seed=seed, n_swipes=n_swipes, policy="model",
                ))
            )
            # Random control uses its own fresh user so its seen-set/decay don't touch the model run.
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            uid_r, _ = insert_user(conn, f"sla_reg_rand_{i}")
            user_r = get_user(conn, uid_r)
            conn.close()
            random_runs.append(
                asyncio.run(registered_trajectory(
                    db_path, user_r, user_proto, model_service,
                    seed=seed, n_swipes=n_swipes, policy="random",
                ))
            )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    return _summarize(model_runs, random_runs)


def _print_report(label: str, m: dict, last10_bar: float, lift_bar: float) -> None:
    last_ok = "PASS" if m["last_10_hit_rate"] >= last10_bar else "FAIL"
    lift_ok = "PASS" if m["lift"] >= lift_bar else "FAIL"
    print(f"\n{'='*60}\n{label}  ({m['runs']} runs)")
    print(f"  last_10 hit-rate : {m['last_10_hit_rate']:.1%}  (bar >= {last10_bar:.0%})  [{last_ok}]")
    print(f"  model overall    : {m['model_overall']:.1%}")
    print(f"  random overall   : {m['random_overall']:.1%}")
    print(f"  lift             : {m['lift']:+.1%}  (bar >= +{lift_bar:.0%})  [{lift_ok}]")
    print(f"  model wins       : {m['model_wins']}/{m['runs']}")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Model accuracy SLA sweep (ADR-0009)")
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS)
    parser.add_argument("--swipes", type=int, default=DEFAULT_SWIPES)
    parser.add_argument("--profile", choices=["picky", "easy"], default="picky")
    parser.add_argument("--guest-only", action="store_true")
    parser.add_argument("--registered-only", action="store_true")
    args = parser.parse_args()

    if not real_db_available():
        print("real cravings.db not present or too small — cannot run SLA sweep")
        raise SystemExit(1)

    if not args.registered_only:
        _print_report(
            "GUEST learning SLA",
            evaluate_guest(args.runs, args.swipes, profile=args.profile),
            last10_bar=0.60, lift_bar=0.10,
        )
    if not args.guest_only:
        _print_report(
            "REGISTERED learning SLA",
            evaluate_registered(args.runs, args.swipes, profile=args.profile),
            last10_bar=0.60, lift_bar=0.10,
        )


if __name__ == "__main__":
    main()
