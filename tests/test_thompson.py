"""Tests for Thompson Sampling model."""

import tempfile
from pathlib import Path

import numpy as np
import pytest

from model.thompson import ThompsonSamplingModel, ModelConfig
from model.features import TOTAL_DIM, CONTINUOUS_ATTRS


@pytest.fixture
def model():
    return ThompsonSamplingModel()


@pytest.fixture
def sample_item():
    return {
        "spice_level": 0.7,
        "sweetness": 0.2,
        "sourness": 0.3,
        "savory_umami": 0.8,
        "saltiness": 0.5,
        "bitterness": 0.1,
        "temperature": 0.9,
        "texture_softness": 0.6,
        "sauce_heaviness": 0.7,
        "richness": 0.6,
        "veggie_density": 0.2,
        "dairy_content": 0.3,
        "smell_intensity": 0.5,
        "nausea_trigger": 0.1,
        "protein_type": "chicken",
        "cuisine_type": "indian",
        "carb_base": "rice",
    }


@pytest.fixture
def sample_context():
    return {
        "dietary_mode": "standard",
        "hour": 19.0,
        "mood": "comfort",
        "recent_rejection_rate": 0.0,
        "days_since_last_session": 0.0,
    }


class TestModelInit:
    def test_default_dimensions(self, model):
        assert model.mu.shape == (TOTAL_DIM,)
        assert model.B.shape == (TOTAL_DIM, TOTAL_DIM)

    def test_zero_initial_mean(self, model):
        assert np.allclose(model.mu, 0.0)

    def test_initial_precision_is_scaled_identity(self, model):
        expected = np.eye(TOTAL_DIM) * model.config.prior_precision
        assert np.allclose(model.B, expected)

    def test_zero_swipes_initially(self, model):
        assert model.total_swipes == 0


class TestScoring:
    def test_returns_sorted_scores(self, model, sample_item, sample_context):
        items = [sample_item, {**sample_item, "spice_level": 0.1}, {**sample_item, "sweetness": 0.9}]
        scores = model.score_items(items, sample_context)
        assert len(scores) == 3
        # Scores should be sorted descending
        score_vals = [s[1] for s in scores]
        assert score_vals == sorted(score_vals, reverse=True)

    def test_scores_between_0_and_1(self, model, sample_item, sample_context):
        scores = model.score_items([sample_item], sample_context)
        assert 0.0 <= scores[0][1] <= 1.0

    def test_recommendation_returns_valid_index(self, model, sample_item, sample_context):
        items = [sample_item, {**sample_item, "cuisine_type": "thai"}]
        idx = model.get_recommendation(items, sample_context)
        assert 0 <= idx < len(items)


class TestRecordSwipe:
    def test_updates_swipe_count(self, model, sample_item, sample_context):
        model.record_swipe(sample_item, sample_context, 1)
        assert model.total_swipes == 1

    def test_updates_precision_matrix(self, model, sample_item, sample_context):
        B_before = model.B.copy()
        model.record_swipe(sample_item, sample_context, 1)
        assert not np.allclose(model.B, B_before)

    def test_positive_swipe_shifts_mean(self, model, sample_item, sample_context):
        mu_before = model.mu.copy()
        model.record_swipe(sample_item, sample_context, 1)
        # Mean should change after swipe
        assert not np.allclose(model.mu, mu_before)

    def test_multiple_swipes_accumulate(self, model, sample_item, sample_context):
        for _ in range(5):
            model.record_swipe(sample_item, sample_context, 1)
        assert model.total_swipes == 5


class TestExplorationControl:
    def test_alpha_initial_phase(self):
        model = ThompsonSamplingModel()
        model.total_swipes = 5
        assert model._get_alpha() == 1.0

    def test_alpha_learning_phase(self):
        model = ThompsonSamplingModel()
        model.total_swipes = 50
        assert model._get_alpha() == 0.5

    def test_alpha_exploitation_phase(self):
        model = ThompsonSamplingModel()
        model.total_swipes = 150
        assert model._get_alpha() == 0.3

    def test_drift_detection_raises_alpha(self):
        model = ThompsonSamplingModel()
        model.total_swipes = 150
        alpha = model._get_alpha(recent_rejection_rate=0.7)
        assert alpha == 0.8

    def test_drift_recovery(self):
        model = ThompsonSamplingModel()
        model.total_swipes = 150
        # Trigger drift
        model._get_alpha(recent_rejection_rate=0.7)
        assert model._drift_active
        # Recover (below threshold - 0.1)
        model._get_alpha(recent_rejection_rate=0.4)
        assert not model._drift_active


class TestDecay:
    def test_decay_factor_current(self, model):
        assert model._decay_factor(0) == 1.0

    def test_decay_factor_decreases(self, model):
        d1 = model._decay_factor(10)
        d2 = model._decay_factor(100)
        assert d1 > d2

    def test_apply_decay_modifies_precision(self, model, sample_item, sample_context):
        # First add some data so B isn't just scaled identity
        for _ in range(5):
            model.record_swipe(sample_item, sample_context, 1)
        B_before = model.B.copy()
        model.apply_decay()
        assert not np.allclose(model.B, B_before)

    def test_maybe_apply_decay_skips_if_recent(self, model):
        import time
        model.last_decay_ts = time.time()  # just decayed
        days = model.maybe_apply_decay()
        assert days == 0.0

    def test_maybe_apply_decay_runs_if_stale(self, model, sample_item, sample_context):
        for _ in range(5):
            model.record_swipe(sample_item, sample_context, 1)
        # Force "stale" by backdating last_decay_ts 2 days
        model.last_decay_ts -= 2 * 86400
        B_before = model.B.copy()
        days = model.maybe_apply_decay()
        assert days > 1.5  # ~2 days
        assert not np.allclose(model.B, B_before)

    def test_apply_decay_zero_days_noop(self, model, sample_item, sample_context):
        for _ in range(5):
            model.record_swipe(sample_item, sample_context, 1)
        B_before = model.B.copy()
        model.apply_decay(0.0)
        assert np.allclose(model.B, B_before)


class TestColdStart:
    def test_onboarding_sets_prior(self, model):
        model.set_prior_from_onboarding({"spice_level": 0.8, "sweetness": -0.5})
        # spice_level is index 0 in CONTINUOUS_ATTRS
        assert model.mu[0] > 0
        # sweetness is index 1
        assert model.mu[1] < 0

    def test_onboarding_ignores_unknown_attrs(self, model):
        mu_before = model.mu.copy()
        model.set_prior_from_onboarding({"not_a_real_attr": 1.0})
        assert np.allclose(model.mu, mu_before)

    def test_onboarding_moderate_strength(self, model):
        model.set_prior_from_onboarding({"spice_level": 1.0})
        # Should be scaled by prior_strength (0.5), not raw value
        assert model.mu[0] == 0.5


class TestPersistence:
    def test_save_and_load(self, model, sample_item, sample_context):
        # Train a bit
        for _ in range(5):
            model.record_swipe(sample_item, sample_context, 1)

        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            path = f.name

        try:
            model.save(path)

            loaded = ThompsonSamplingModel()
            loaded.load(path)

            assert np.allclose(loaded.mu, model.mu)
            assert np.allclose(loaded.B, model.B)
            assert loaded.total_swipes == model.total_swipes
        finally:
            Path(path).unlink(missing_ok=True)
