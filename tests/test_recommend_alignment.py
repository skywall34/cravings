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
