"""Feature engineering: food attributes + context → model feature vector."""

import math
import os
from dataclasses import dataclass, field

import numpy as np

# Toggle interaction terms via env var. Off by default — synthetic-user A/B
# (Apr 2026) showed interactions HURT when user has no context-dependent prefs.
# Enable for users whose time-of-day preferences clearly differ.
USE_INTERACTIONS = os.environ.get("CRAVINGS_USE_INTERACTIONS", "0") == "1"

# Categorical value mappings (order matters — defines one-hot positions)
PROTEIN_TYPES = ["chicken", "beef", "pork", "fish", "shellfish", "egg", "tofu_plant", "legume", "none"]
CUISINE_TYPES = [
    "american", "mexican", "italian", "chinese", "japanese",
    "thai", "indian", "korean", "mediterranean", "middle_eastern",
    "french", "spanish", "german", "eastern_european",
    "vietnamese", "filipino", "indonesian", "brazilian", "caribbean", "ethiopian",
    "other",
]
CARB_BASES = ["rice", "noodles_pasta", "bread", "potato", "tortilla", "none"]

# Continuous food attribute columns (in order)
CONTINUOUS_ATTRS = [
    "spice_level", "sweetness", "sourness", "savory_umami", "saltiness", "bitterness",
    "temperature", "texture_softness", "sauce_heaviness", "richness",
    "veggie_density", "dairy_content", "smell_intensity", "nausea_trigger",
]

# Curated food×context interaction terms.
# Each entry: (food_attr, context_kind, context_key) — multiplied at encode time.
# context_kind ∈ {"time_sin", "time_cos"}.
# Chosen for high-signal pairs (warm food at night, etc.); avoids full cross.
INTERACTION_TERMS = [
    ("temperature", "time_sin", None),
    ("temperature", "time_cos", None),
]

# Dimensions: 14 continuous + 9 protein + 21 cuisine + 6 carb = 50 food dims
FOOD_DIM = len(CONTINUOUS_ATTRS) + len(PROTEIN_TYPES) + len(CUISINE_TYPES) + len(CARB_BASES)
# Context: 2 time_of_day + 1 rejection_rate + 1 days_since = 4
CONTEXT_DIM = 2 + 2
INTERACTION_DIM = len(INTERACTION_TERMS) if USE_INTERACTIONS else 0
# Total
TOTAL_DIM = FOOD_DIM + CONTEXT_DIM + INTERACTION_DIM


def one_hot(value: str, categories: list[str]) -> np.ndarray:
    vec = np.zeros(len(categories))
    if value not in categories:
        raise ValueError(f"Unknown category {value!r}; expected one of {categories}")
    vec[categories.index(value)] = 1.0
    return vec


@dataclass
class FeatureSchema:
    """Single source of truth for feature dimensionality and model validation.

    Use validate_model() after loading a persisted ThompsonSamplingModel to catch
    schema drift (e.g. model trained with interactions ON loaded with flag OFF).
    """
    use_interactions: bool = field(default_factory=lambda: USE_INTERACTIONS)

    @property
    def food_dim(self) -> int:
        return len(CONTINUOUS_ATTRS) + len(PROTEIN_TYPES) + len(CUISINE_TYPES) + len(CARB_BASES)

    @property
    def context_dim(self) -> int:
        return 2 + 2

    @property
    def interaction_dim(self) -> int:
        return len(INTERACTION_TERMS) if self.use_interactions else 0

    @property
    def total_dim(self) -> int:
        return self.food_dim + self.context_dim + self.interaction_dim

    def validate_model(self, model) -> bool:
        """Returns True if dims match. False signals stale blob — caller should reset to fresh prior."""
        return len(model.mu) == self.total_dim


def encode_food_item(item: dict) -> np.ndarray:
    """Convert food item dict (from DB row) to feature vector."""
    continuous = np.array([float(item.get(attr, 0.0) or 0.0) for attr in CONTINUOUS_ATTRS])
    # `or default` (not `.get(k, default)`): a DB row always carries the key, so a
    # NULL column surfaces as an explicit None that the get-default never catches —
    # one_hot(None) would then 500 the whole recommend request.
    protein = one_hot(item.get("protein_type") or "none", PROTEIN_TYPES)
    cuisine = one_hot(item.get("cuisine_type") or "other", CUISINE_TYPES)
    carb = one_hot(item.get("carb_base") or "none", CARB_BASES)
    return np.concatenate([continuous, protein, cuisine, carb])


def encode_context(
    hour: float = 12.0,
    recent_rejection_rate: float = 0.0,
    days_since_last_session: float = 0.0,
) -> np.ndarray:
    """Encode context features into vector."""
    # Cyclical time encoding
    time_sin = math.sin(2 * math.pi * hour / 24.0)
    time_cos = math.cos(2 * math.pi * hour / 24.0)
    return np.concatenate([
        [time_sin, time_cos],
        [recent_rejection_rate, days_since_last_session],
    ])


def encode_interactions(item: dict, context: dict) -> np.ndarray:
    """Compute curated food×context interaction terms."""
    hour = float(context.get("hour", 12.0))
    time_sin = math.sin(2 * math.pi * hour / 24.0)
    time_cos = math.cos(2 * math.pi * hour / 24.0)

    out = np.zeros(len(INTERACTION_TERMS))
    for i, (attr, kind, key) in enumerate(INTERACTION_TERMS):
        food_val = float(item.get(attr, 0.0) or 0.0)
        if kind == "time_sin":
            ctx_val = time_sin
        elif kind == "time_cos":
            ctx_val = time_cos
        else:
            ctx_val = 0.0
        out[i] = food_val * ctx_val
    return out


def build_feature_vector(item: dict, context: dict) -> np.ndarray:
    """Combine food item features + context (+ interactions if enabled)."""
    food = encode_food_item(item)
    ctx = encode_context(**context)
    if USE_INTERACTIONS:
        inter = encode_interactions(item, context)
        return np.concatenate([food, ctx, inter])
    return np.concatenate([food, ctx])
