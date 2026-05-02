"""Simulation: validate Thompson Sampling learns synthetic preferences in <20 swipes.

Creates a synthetic user with known preferences, runs swipe simulation against
the food items in the database, and measures hit rate convergence.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from scipy.special import expit

from db.database import init_db
from model.features import build_feature_vector, CONTINUOUS_ATTRS
from model.thompson import ThompsonSamplingModel, ModelConfig


def create_synthetic_user(seed: int = 42, profile: str = "picky") -> dict:
    """Define a synthetic user with clear preferences.

    profile="picky": polarized preferences, low base rate (~30-50% random hit).
        Strong likes: very spicy, very savory, hot, saucy (Thai/Indian/Korean).
        Strong dislikes: sweet, cold, dairy-heavy, light/veggie-only.
    profile="easy": original mild user (~75% random hit, ceiling effect).
    """
    if profile == "easy":
        prefs = {
            "spice_level": 0.8, "sweetness": -0.6, "sourness": 0.3,
            "savory_umami": 0.7, "saltiness": 0.3, "bitterness": -0.2,
            "temperature": 0.6, "texture_softness": 0.2,
            "sauce_heaviness": 0.5, "richness": 0.4,
            "veggie_density": -0.1, "dairy_content": 0.0,
            "smell_intensity": 0.3, "nausea_trigger": -0.5,
        }
        bias = 0.0
    else:  # picky — polarized, with negative bias to suppress base rate
        prefs = {
            "spice_level": 2.0, "sweetness": -2.0, "sourness": 0.0,
            "savory_umami": 2.0, "saltiness": 0.5, "bitterness": -1.0,
            "temperature": 1.5, "texture_softness": -0.5,
            "sauce_heaviness": 1.0, "richness": 0.5,
            "veggie_density": -1.5, "dairy_content": -1.5,
            "smell_intensity": 0.5, "nausea_trigger": -1.5,
        }
        bias = -1.5  # makes random food ~30% positive

    return {
        "preferences": prefs,
        "bias": bias,
        "noise": 0.1,
        "context": {
            "dietary_mode": "standard",
            "hour": 19.0,
            "mood": "adventurous",
            "recent_rejection_rate": 0.0,
            "days_since_last_session": 0.0,
        },
    }


def synthetic_swipe(user: dict, item: dict, rng: np.random.Generator) -> int:
    """Simulate user swipe based on hidden preference weights."""
    prefs = user["preferences"]
    score = user.get("bias", 0.0)
    for attr, weight in prefs.items():
        val = float(item.get(attr, 0.0) or 0.0)
        score += weight * val
    score += rng.normal(0, user["noise"])
    prob = expit(score)
    return int(rng.random() < prob)


def load_food_items_from_db(db_path: Path | None = None) -> list[dict]:
    """Load tagged food items from database."""
    conn = init_db(db_path) if db_path else init_db()
    rows = conn.execute(
        "SELECT * FROM food_items WHERE tagging_status = 'tagged'"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def run_simulation(
    n_swipes: int = 50,
    pool_size: int = 10,
    seed: int = 42,
    db_path: Path | None = None,
    use_onboarding: bool = False,
    verbose: bool = True,
    policy: str = "model",
    profile: str = "picky",
) -> dict:
    """Run swipe simulation and track hit rate.

    Args:
        n_swipes: total swipes to simulate
        pool_size: candidates shown per round
        seed: random seed
        db_path: optional DB path
        use_onboarding: whether to set prior from onboarding
        verbose: print progress
    """
    rng = np.random.default_rng(seed)
    user = create_synthetic_user(seed, profile=profile)
    items = load_food_items_from_db(db_path)

    if len(items) < pool_size:
        print(f"Only {len(items)} tagged items in DB, need at least {pool_size}")
        return {}

    model = ThompsonSamplingModel(ModelConfig())

    if use_onboarding:
        model.set_prior_from_onboarding({
            "spice_level": 0.5,
            "savory_umami": 0.5,
            "sweetness": -0.3,
        })

    context = user["context"]
    hits = []
    cumulative_hits = []
    window_size = 5
    seen_ids: set[int] = set()

    for swipe_num in range(n_swipes):
        # Candidate pool: random subset from items NOT yet swiped this session
        unseen_indices = [i for i, it in enumerate(items) if it["id"] not in seen_ids]
        if not unseen_indices:
            if verbose:
                print(f"  Pool exhausted at swipe {swipe_num + 1}; stopping")
            break
        sample_size = min(pool_size, len(unseen_indices))
        indices = rng.choice(unseen_indices, size=sample_size, replace=False)
        candidates = [items[i] for i in indices]

        # Pick item
        if policy == "random":
            rec_idx = int(rng.integers(0, len(candidates)))
        else:
            rec_idx = model.get_recommendation(candidates, context)
        chosen = candidates[rec_idx]

        # Simulate user response
        reward = synthetic_swipe(user, chosen, rng)
        hits.append(reward)

        # Mark seen
        seen_ids.add(chosen["id"])

        # Update model
        model.record_swipe(chosen, context, reward)

        # Track rolling hit rate
        recent = hits[max(0, len(hits) - window_size):]
        rolling_rate = sum(recent) / len(recent)

        # Update context rejection rate
        recent_for_context = hits[max(0, len(hits) - 10):]
        context["recent_rejection_rate"] = 1.0 - (sum(recent_for_context) / len(recent_for_context))

        cumulative_rate = sum(hits) / len(hits)
        cumulative_hits.append(cumulative_rate)

        if verbose:
            marker = "✓" if reward else "✗"
            print(
                f"  Swipe {swipe_num + 1:3d}: {chosen['name']:30s} "
                f"{marker}  rolling={rolling_rate:.0%}  cumulative={cumulative_rate:.0%}  "
                f"α={model._get_alpha(context['recent_rejection_rate']):.1f}"
            )

    # Summary
    first_10 = sum(hits[:10]) / 10
    last_10 = sum(hits[-10:]) / 10
    overall = sum(hits) / len(hits)

    results = {
        "total_swipes": n_swipes,
        "overall_hit_rate": overall,
        "first_10_hit_rate": first_10,
        "last_10_hit_rate": last_10,
        "improvement": last_10 - first_10,
        "hits": hits,
        "cumulative_hits": cumulative_hits,
        "total_model_swipes": model.total_swipes,
    }

    if verbose:
        print(f"\n{'='*60}")
        print(f"Results ({n_swipes} swipes, pool_size={pool_size}):")
        print(f"  First 10 hit rate: {first_10:.0%}")
        print(f"  Last 10 hit rate:  {last_10:.0%}")
        print(f"  Overall:           {overall:.0%}")
        print(f"  Improvement:       {results['improvement']:+.0%}")
        learned = last_10 > first_10 and last_10 >= 0.6
        print(f"  Learned in <20?    {'YES' if learned and n_swipes <= 20 else 'checking...'}")

    return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Thompson Sampling simulation")
    parser.add_argument("--swipes", type=int, default=50, help="Number of swipes")
    parser.add_argument("--pool", type=int, default=10, help="Candidate pool size")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--db", type=str, help="Database path")
    parser.add_argument("--onboarding", action="store_true", help="Use onboarding prior")
    parser.add_argument("--runs", type=int, default=1, help="Number of runs to average")
    parser.add_argument("--policy", choices=["model", "random"], default="model",
                        help="Recommendation policy (model = TS, random = baseline)")
    parser.add_argument("--compare", action="store_true",
                        help="Run both policies for each seed and report delta")
    parser.add_argument("--profile", choices=["picky", "easy"], default="picky",
                        help="Synthetic user profile")
    args = parser.parse_args()

    db_path = Path(args.db) if args.db else None

    if args.compare:
        model_overall = []
        random_overall = []
        for run in range(args.runs):
            seed = args.seed + run
            m = run_simulation(args.swipes, args.pool, seed, db_path, args.onboarding,
                               verbose=False, policy="model", profile=args.profile)
            r = run_simulation(args.swipes, args.pool, seed, db_path, args.onboarding,
                               verbose=False, policy="random", profile=args.profile)
            model_overall.append(m["overall_hit_rate"])
            random_overall.append(r["overall_hit_rate"])
            print(f"  Run {run + 1}: model={m['overall_hit_rate']:.0%}  "
                  f"random={r['overall_hit_rate']:.0%}  Δ={m['overall_hit_rate'] - r['overall_hit_rate']:+.0%}")
        print(f"\n{'='*60}")
        print(f"Average over {args.runs} runs (model vs random):")
        print(f"  Model:  {np.mean(model_overall):.1%}")
        print(f"  Random: {np.mean(random_overall):.1%}")
        print(f"  Lift:   {np.mean(model_overall) - np.mean(random_overall):+.1%}")
    elif args.runs == 1:
        run_simulation(args.swipes, args.pool, args.seed, db_path, args.onboarding,
                       policy=args.policy, profile=args.profile)
    else:
        all_results = []
        for run in range(args.runs):
            print(f"\n--- Run {run + 1}/{args.runs} ---")
            r = run_simulation(args.swipes, args.pool, args.seed + run, db_path,
                               args.onboarding, verbose=False, policy=args.policy,
                               profile=args.profile)
            all_results.append(r)
            print(f"  First 10: {r['first_10_hit_rate']:.0%}  Last 10: {r['last_10_hit_rate']:.0%}  Δ: {r['improvement']:+.0%}")

        avg_first = np.mean([r["first_10_hit_rate"] for r in all_results])
        avg_last = np.mean([r["last_10_hit_rate"] for r in all_results])
        avg_improvement = np.mean([r["improvement"] for r in all_results])
        avg_overall = np.mean([r["overall_hit_rate"] for r in all_results])
        print(f"\n{'='*60}")
        print(f"Average over {args.runs} runs ({args.policy}):")
        print(f"  Overall:  {avg_overall:.1%}")
        print(f"  First 10: {avg_first:.0%}")
        print(f"  Last 10:  {avg_last:.0%}")
        print(f"  Avg improvement: {avg_improvement:+.0%}")


if __name__ == "__main__":
    main()
