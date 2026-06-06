"""Contextual Thompson Sampling with Bayesian logistic regression.

Maintains posterior N(μ, B⁻¹) over weight vector w.
- Scoring: P(swipe_right | z) = σ(wᵀz) where z = food_features + context
- Update: Sherman-Morrison rank-1 update on precision matrix B
- Exploration: adaptive α controls posterior sampling variance
- Decay: exponential decay on historical data (~14-day half-life)
"""

import math
import pickle
import time
from dataclasses import dataclass, field

import numpy as np
from scipy.special import expit  # sigmoid

from model.features import TOTAL_DIM, build_feature_vector


@dataclass
class ModelConfig:
    dim: int = TOTAL_DIM
    prior_precision: float = 0.25  # λ₀ — prior precision (regularization)
    alpha_schedule: dict = field(default_factory=lambda: {
        0: 1.0,     # swipes 0-19: high exploration
        20: 0.5,    # swipes 20-99: balanced
        100: 0.3,   # swipes 100+: mostly exploit
    })
    drift_reset_alpha: float = 0.8  # α when drift detected
    drift_threshold: float = 0.6    # rejection rate triggering drift
    decay_half_life_days: float = 14.0
    swipes_per_day: float = 7.0     # assumed avg for decay calc
    decay_min_interval_seconds: float = 6 * 3600  # don't apply decay more than once per 6h


class ThompsonSamplingModel:
    def __init__(self, config: ModelConfig | None = None):
        self.config = config or ModelConfig()
        d = self.config.dim
        # Posterior: N(mu, B⁻¹)
        self.mu = np.zeros(d)
        self.B = np.eye(d) * self.config.prior_precision
        self.total_swipes = 0
        self._drift_active = False
        self.last_decay_ts: float = time.time()

    def _get_alpha(self, recent_rejection_rate: float = 0.0) -> float:
        """Get exploration parameter based on swipe count and drift detection."""
        if recent_rejection_rate >= self.config.drift_threshold:
            self._drift_active = True
            return self.config.drift_reset_alpha

        if self._drift_active and recent_rejection_rate < self.config.drift_threshold - 0.1:
            self._drift_active = False

        if self._drift_active:
            return self.config.drift_reset_alpha

        # Schedule lookup
        alpha = 1.0
        for threshold, value in sorted(self.config.alpha_schedule.items()):
            if self.total_swipes >= threshold:
                alpha = value
        return alpha

    def _decay_factor(self, steps_ago: int = 0) -> float:
        """Exponential decay weight for a swipe that happened steps_ago swipes ago."""
        if steps_ago <= 0:
            return 1.0
        half_life_swipes = self.config.decay_half_life_days * self.config.swipes_per_day
        return math.pow(0.5, steps_ago / half_life_swipes)

    def score_items(self, items: list[dict], context: dict) -> list[tuple[int, float]]:
        """Score candidate items. Returns list of (item_index, score) sorted descending."""
        alpha = self._get_alpha(context.get("recent_rejection_rate", 0.0))

        # Sample weight vector from posterior
        B_inv = np.linalg.inv(self.B)
        cov = alpha ** 2 * B_inv
        w_sample = np.random.multivariate_normal(self.mu, cov)

        scores = []
        for i, item in enumerate(items):
            z = build_feature_vector(item, context)
            score = expit(w_sample @ z)
            scores.append((i, float(score)))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def get_recommendation(self, items: list[dict], context: dict) -> int:
        """Return index of top-recommended item."""
        scores = self.score_items(items, context)
        return scores[0][0]

    def record_swipe(self, item: dict, context: dict, reward: float) -> None:
        """Update posterior after observing swipe (reward=1 right, 0 left).

        Uses Laplace approximation update:
        B_{t+1} = B_t + p(1-p) * z zᵀ  (Sherman-Morrison)
        μ_{t+1} = μ_t + B_{t+1}⁻¹ z (r - p)
        where p = σ(μᵀz)
        """
        z = build_feature_vector(item, context)
        p = expit(self.mu @ z)

        # Decay factor (current swipe has no decay)
        decay = 1.0

        # Hessian contribution: p(1-p) * z zᵀ
        h = p * (1 - p) * decay
        self.B += h * np.outer(z, z)

        # Gradient step via Newton-like update
        B_inv = np.linalg.inv(self.B)
        gradient = (reward - p) * z * decay
        self.mu += B_inv @ gradient

        self.total_swipes += 1

    def apply_decay(self, days: float = 1.0) -> None:
        """Apply exponential decay over `days` of elapsed time.

        Shrinks B toward prior, effectively down-weighting old observations.
        Use days=1 for nightly cron, or pass actual elapsed days for catch-up.
        """
        if days <= 0:
            return
        decay = math.pow(0.5, days / self.config.decay_half_life_days)
        self.B = decay * self.B + (1 - decay) * np.eye(self.config.dim) * self.config.prior_precision

    def maybe_apply_decay(self, now: float | None = None) -> float:
        """Apply decay if enough time has elapsed since last_decay_ts.

        Returns the number of days decayed (0 if skipped). Idempotent —
        safe to call on every recommendation request.
        """
        now = now if now is not None else time.time()
        elapsed_s = now - self.last_decay_ts
        if elapsed_s < self.config.decay_min_interval_seconds:
            return 0.0
        days = elapsed_s / 86400.0
        self.apply_decay(days)
        self.last_decay_ts = now
        return days

    def reset(self) -> None:
        """Wipe learned posterior back to uninformed prior. Use before re-seeding from new taste sliders."""
        d = self.config.dim
        self.mu = np.zeros(d)
        self.B = np.eye(d) * self.config.prior_precision
        self.total_swipes = 0
        self._drift_active = False
        self.last_decay_ts = time.time()

    def set_prior_from_onboarding(self, preferences: dict) -> None:
        """Initialize prior mean from onboarding selections.

        preferences: dict mapping attribute names to preference signals.
        E.g., {"spice_level": -0.5, "sourness": 0.8, "smell_intensity": -1.0}
        Positive = craving, negative = aversion. Values should be in [-1, 1].
        """
        from model.features import CONTINUOUS_ATTRS
        prior_strength = 0.5  # moderate — easily overridden by swipes
        for attr, signal in preferences.items():
            if attr in CONTINUOUS_ATTRS:
                idx = CONTINUOUS_ATTRS.index(attr)
                self.mu[idx] = signal * prior_strength

    def save(self, path: str) -> None:
        state = {
            "mu": self.mu,
            "B": self.B,
            "total_swipes": self.total_swipes,
            "config": self.config,
            "_drift_active": self._drift_active,
            "last_decay_ts": self.last_decay_ts,
        }
        with open(path, "wb") as f:
            pickle.dump(state, f)

    def load(self, path: str) -> None:
        with open(path, "rb") as f:
            state = pickle.load(f)
        self.mu = state["mu"]
        self.B = state["B"]
        self.total_swipes = state["total_swipes"]
        self.config = state["config"]
        self._drift_active = state["_drift_active"]
        self.last_decay_ts = state.get("last_decay_ts", time.time())
