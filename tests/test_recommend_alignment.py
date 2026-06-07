"""Statistical alignment tests: do onboarding sliders actually steer the FIRST recommendation?

Thompson sampling is stochastic — a single draw proves nothing. These tests run many
fresh first-session draws and measure the *fraction* of times the top-ranked dish matches
the slider the guest set. This is the direct measure of the reported bug ("spicy user gets
sweet food on the first card").

Current code is expected to FAIL T2.1/T2.2/T2.3 (alignment ~0.55, near coin-flip) because
first-session sampling variance swamps the seeded prior. The control T2.4 should pass.
After the model fix, all should pass.
"""

import numpy as np
import pytest

from model.features import CONTINUOUS_ATTRS
from model.thompson import ThompsonSamplingModel

# How many fresh first-session draws per measurement. Higher = tighter estimate.
N_DRAWS = 500
# Required fraction of draws where the top dish matches the slider.
ALIGN_THRESHOLD = 0.80

# First-session context: no swipes seen, neutral mood/time.
FIRST_SESSION_CTX = {
    "dietary_mode": "standard",
    "hour": 12.0,
    "mood": "no_preference",
    "recent_rejection_rate": 0.0,
    "days_since_last_session": 0.0,
}


def make_attr_spread_pool(attr: str, n: int, seed: int) -> list[dict]:
    """Build n synthetic dishes where `attr` is spread uniformly across [0, 1] and every
    other continuous attribute is random noise. Categorical fields use valid enum values
    (one_hot raises on unknowns). This isolates one taste dimension for measurement."""
    rng = np.random.default_rng(seed)
    spread = np.linspace(0.0, 1.0, n)
    rng.shuffle(spread)
    pool = []
    for i in range(n):
        dish = {a: float(rng.random()) for a in CONTINUOUS_ATTRS}
        dish[attr] = float(spread[i])
        dish.update({
            "id": i,
            "name": f"dish_{i}",
            "protein_type": "chicken",
            "cuisine_type": "other",
            "carb_base": "rice",
        })
        pool.append(dish)
    return pool


def fresh_first_session_model(taste_prefs: dict) -> ThompsonSamplingModel:
    """Mirror the guest path: brand-new model seeded only from onboarding sliders."""
    model = ThompsonSamplingModel()
    model.set_prior_from_onboarding(taste_prefs)
    return model


def measure_alignment(taste_prefs: dict, attr: str, pool: list[dict], *, want_high: bool) -> float:
    """Run N_DRAWS independent first-session top-1 picks. Return the fraction whose top
    dish lands on the correct side of the pool's median for `attr`."""
    median = float(np.median([d[attr] for d in pool]))
    hits = 0
    for draw in range(N_DRAWS):
        np.random.seed(10_000 + draw)  # score_items uses global np.random; vary per draw
        model = fresh_first_session_model(taste_prefs)
        ranked = model.score_items(pool, FIRST_SESSION_CTX)
        top_idx = ranked[0][0]
        top_val = pool[top_idx][attr]
        if (top_val >= median) == want_high:
            hits += 1
    return hits / N_DRAWS


# ---------------------------------------------------------------------------
# T2.1 — single positive slider (the headline bug: "I want spicy")
# ---------------------------------------------------------------------------
def test_spicy_slider_yields_spicy_first_card():
    pool = make_attr_spread_pool("spice_level", n=50, seed=1)
    frac = measure_alignment({"spice_level": 1.0}, "spice_level", pool, want_high=True)
    assert frac >= ALIGN_THRESHOLD, (
        f"Spicy guest got a spicy top card only {frac:.0%} of first sessions "
        f"(need >={ALIGN_THRESHOLD:.0%}). Sampling noise is swamping the slider."
    )


# ---------------------------------------------------------------------------
# T2.2 — every slider dimension, independently
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("attr", ["spice_level", "sweetness", "sourness", "texture_softness", "richness"])
def test_each_slider_steers_first_card(attr):
    pool = make_attr_spread_pool(attr, n=50, seed=2)
    frac = measure_alignment({attr: 1.0}, attr, pool, want_high=True)
    assert frac >= ALIGN_THRESHOLD, (
        f"Maxed '{attr}' slider matched the top card only {frac:.0%} (need >={ALIGN_THRESHOLD:.0%})."
    )


# ---------------------------------------------------------------------------
# T2.3 — conflicting prefs: crave spice, avoid sweet
# ---------------------------------------------------------------------------
def test_conflicting_prefs_respect_both():
    prefs = {"spice_level": 1.0, "sweetness": -1.0}
    rng = np.random.default_rng(3)
    # Pool where spice and sweetness vary independently so "high spice" != "low sweet" by construction.
    pool = []
    for i in range(50):
        dish = {a: float(rng.random()) for a in CONTINUOUS_ATTRS}
        dish.update({"id": i, "name": f"d{i}", "protein_type": "chicken",
                     "cuisine_type": "other", "carb_base": "rice"})
        pool.append(dish)

    top_spice, top_sweet = [], []
    for draw in range(N_DRAWS):
        np.random.seed(20_000 + draw)
        model = fresh_first_session_model(prefs)
        top_idx = model.score_items(pool, FIRST_SESSION_CTX)[0][0]
        top_spice.append(pool[top_idx]["spice_level"])
        top_sweet.append(pool[top_idx]["sweetness"])

    mean_spice, mean_sweet = np.mean(top_spice), np.mean(top_sweet)
    assert mean_spice > 0.5, f"Crave-spice ignored: mean top spice {mean_spice:.2f} (want >0.5)."
    assert mean_sweet < 0.5, f"Avoid-sweet ignored: mean top sweet {mean_sweet:.2f} (want <0.5)."


# ---------------------------------------------------------------------------
# T2.4 — control: neutral sliders => no bias (~50/50). Guards against over-correction.
# ---------------------------------------------------------------------------
def test_neutral_sliders_have_no_bias():
    pool = make_attr_spread_pool("spice_level", n=50, seed=4)
    frac = measure_alignment({}, "spice_level", pool, want_high=True)
    assert 0.40 <= frac <= 0.60, (
        f"Neutral guest showed {frac:.0%} high-spice bias (want ~50%). "
        f"Fix should not hard-bias when no slider is set."
    )


# ===========================================================================
# T2.5–T2.7 — COMBINATION sliders (multiple attrs at once, graded magnitudes)
# These check the model honors slider *combinations* and their *relative
# strengths*, not just one maxed dimension. Averaged over several independent
# pools so the assertions aren't a single-pool artifact (equal-signal cases are
# symmetric, so per-pool ordering is noisy — only joint lift / magnitude
# ordering is robust).
# ===========================================================================

def _random_attr_pool(n: int, seed: int) -> list[dict]:
    """n dishes with every continuous attr i.i.d. uniform on [0,1] (median ~0.5),
    so each taste dimension varies independently of the others."""
    rng = np.random.default_rng(seed)
    pool = []
    for i in range(n):
        dish = {a: float(rng.random()) for a in CONTINUOUS_ATTRS}
        dish.update({"id": i, "name": f"d{i}", "protein_type": "chicken",
                     "cuisine_type": "other", "carb_base": "rice"})
        pool.append(dish)
    return pool


def mean_top_attrs(prefs: dict, attrs: list[str], *, pool_seeds=(1, 2, 3), draws=250) -> dict:
    """Mean top-1 value of each attr in `attrs`, averaged over fresh first-session draws
    across several independent pools. Returns {attr: mean_value}."""
    acc = {a: [] for a in attrs}
    for ps in pool_seeds:
        pool = _random_attr_pool(50, ps)
        for d in range(draws):
            np.random.seed(30_000 * ps + d)
            model = fresh_first_session_model(prefs)
            top_idx = model.score_items(pool, FIRST_SESSION_CTX)[0][0]
            for a in attrs:
                acc[a].append(pool[top_idx][a])
    return {a: float(np.mean(v)) for a, v in acc.items()}


# T2.5 — two simultaneous cravings: "sweet AND spicy". Both should be lifted.
def test_co_craving_lifts_both_attributes():
    means = mean_top_attrs({"spice_level": 1.0, "sweetness": 1.0}, ["spice_level", "sweetness"])
    assert means["spice_level"] > 0.60 and means["sweetness"] > 0.60, (
        f"Co-craving (spice+sweet) failed to lift both: {means} (each want >0.60, pool median ~0.50)."
    )


# T2.6 — graded magnitudes: a strong slider should outrank a weak one of the same sign.
# spice=1.0 vs sweetness=0.3 → top cards should skew spicier than they are sweet.
def test_graded_signal_orders_by_magnitude():
    means = mean_top_attrs({"spice_level": 1.0, "sweetness": 0.3}, ["spice_level", "sweetness"])
    assert means["spice_level"] > 0.65, (
        f"Strong slider (spice=1.0) under-weighted: mean {means['spice_level']:.2f} (want >0.65)."
    )
    assert means["spice_level"] > means["sweetness"] + 0.10, (
        f"Model ignored relative slider strength: spice {means['spice_level']:.2f} should clearly "
        f"exceed weaker sweet {means['sweetness']:.2f} (margin >0.10)."
    )


# T2.7 — partial combination with fractional values: richness=0.6, crunchy(texture)=0.4.
# Both lifted above baseline, and the larger slider lands higher.
def test_partial_combo_both_lifted_and_ordered():
    means = mean_top_attrs({"richness": 0.6, "texture_softness": 0.4},
                           ["richness", "texture_softness"])
    assert means["richness"] > 0.55 and means["texture_softness"] > 0.55, (
        f"Partial combo failed to lift both: {means} (each want >0.55)."
    )
    assert means["richness"] > means["texture_softness"], (
        f"Larger slider (richness 0.6) should outrank smaller (texture 0.4): {means}."
    )
