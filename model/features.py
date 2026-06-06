"""Feature engineering: food attributes + context → model feature vector."""

import math
import os
from dataclasses import dataclass, field

import numpy as np

# Toggle interaction terms via env var. Off by default — synthetic-user A/B
# (Apr 2026) showed interactions HURT when user has no context-dependent prefs.
# Enable for users whose mood/time preferences clearly differ.
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
DIETARY_MODES = ["standard", "vegetarian", "vegan", "restricted"]
MOODS = ["comfort", "adventurous", "light_healthy", "no_preference"]

# Continuous food attribute columns (in order)
CONTINUOUS_ATTRS = [
    "spice_level", "sweetness", "sourness", "savory_umami", "saltiness", "bitterness",
    "temperature", "texture_softness", "sauce_heaviness", "richness",
    "veggie_density", "dairy_content", "smell_intensity", "nausea_trigger",
]

# Curated food×context interaction terms.
# Each entry: (food_attr, context_kind, context_key) — multiplied at encode time.
# context_kind ∈ {"mood", "dietary_mode", "time_sin", "time_cos"}.
# Chosen for high-signal pairs (spice/comfort, dairy/vegan, etc.); avoids 143-dim full cross.
INTERACTION_TERMS = [
    ("spice_level", "mood", "comfort"),
    ("spice_level", "mood", "adventurous"),
    ("temperature", "time_sin", None),
    ("temperature", "time_cos", None),
    ("dairy_content", "dietary_mode", "vegan"),
    ("sweetness", "mood", "light_healthy"),
    ("richness", "mood", "comfort"),
    ("veggie_density", "mood", "light_healthy"),
]

# Dimensions: 14 continuous + 9 protein + 21 cuisine + 6 carb = 50 food dims
FOOD_DIM = len(CONTINUOUS_ATTRS) + len(PROTEIN_TYPES) + len(CUISINE_TYPES) + len(CARB_BASES)
# Context: 4 dietary_mode + 2 time_of_day + 4 mood + 1 rejection_rate + 1 days_since = 12
CONTEXT_DIM = len(DIETARY_MODES) + 2 + len(MOODS) + 2
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
        return len(DIETARY_MODES) + 2 + len(MOODS) + 2

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
    protein = one_hot(item.get("protein_type", "none"), PROTEIN_TYPES)
    cuisine = one_hot(item.get("cuisine_type", "other"), CUISINE_TYPES)
    carb = one_hot(item.get("carb_base", "none"), CARB_BASES)
    return np.concatenate([continuous, protein, cuisine, carb])


def encode_context(
    dietary_mode: str = "standard",
    hour: float = 12.0,
    mood: str = "no_preference",
    recent_rejection_rate: float = 0.0,
    days_since_last_session: float = 0.0,
) -> np.ndarray:
    """Encode context features into vector."""
    diet = one_hot(dietary_mode, DIETARY_MODES)
    # Cyclical time encoding
    time_sin = math.sin(2 * math.pi * hour / 24.0)
    time_cos = math.cos(2 * math.pi * hour / 24.0)
    mood_vec = one_hot(mood, MOODS)
    return np.concatenate([
        diet,
        [time_sin, time_cos],
        mood_vec,
        [recent_rejection_rate, days_since_last_session],
    ])


def encode_interactions(item: dict, context: dict) -> np.ndarray:
    """Compute curated food×context interaction terms."""
    hour = float(context.get("hour", 12.0))
    time_sin = math.sin(2 * math.pi * hour / 24.0)
    time_cos = math.cos(2 * math.pi * hour / 24.0)
    mood = context.get("mood", "no_preference")
    dietary_mode = context.get("dietary_mode", "standard")

    out = np.zeros(len(INTERACTION_TERMS))
    for i, (attr, kind, key) in enumerate(INTERACTION_TERMS):
        food_val = float(item.get(attr, 0.0) or 0.0)
        if kind == "mood":
            ctx_val = 1.0 if mood == key else 0.0
        elif kind == "dietary_mode":
            ctx_val = 1.0 if dietary_mode == key else 0.0
        elif kind == "time_sin":
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
