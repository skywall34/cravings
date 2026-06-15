"""Tests for feature engineering module."""

import math
import numpy as np
import pytest

from model.features import (
    one_hot,
    encode_food_item,
    encode_context,
    encode_interactions,
    build_feature_vector,
    FeatureSchema,
    PROTEIN_TYPES,
    CUISINE_TYPES,
    CARB_BASES,
    CONTINUOUS_ATTRS,
    INTERACTION_TERMS,
    FOOD_DIM,
    CONTEXT_DIM,
    INTERACTION_DIM,
    TOTAL_DIM,
)


class TestOneHot:
    def test_valid_value(self):
        vec = one_hot("chicken", PROTEIN_TYPES)
        assert vec[0] == 1.0
        assert sum(vec) == 1.0

    def test_last_value(self):
        vec = one_hot("none", PROTEIN_TYPES)
        assert vec[-1] == 1.0

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError, match="Unknown category"):
            one_hot("dragon", PROTEIN_TYPES)

    def test_correct_length(self):
        assert len(one_hot("beef", PROTEIN_TYPES)) == len(PROTEIN_TYPES)


class TestEncodeFoodItem:
    def test_output_dimension(self):
        item = {"spice_level": 0.5, "protein_type": "chicken", "cuisine_type": "thai", "carb_base": "rice"}
        vec = encode_food_item(item)
        assert len(vec) == FOOD_DIM

    def test_continuous_values_preserved(self):
        item = {"spice_level": 0.7, "sweetness": 0.3}
        vec = encode_food_item(item)
        assert vec[0] == 0.7  # spice_level is first continuous attr
        assert vec[1] == 0.3  # sweetness is second

    def test_missing_values_default_zero(self):
        item = {}
        vec = encode_food_item(item)
        # All continuous should be 0, protein=none, cuisine=other, carb=none
        assert vec[0] == 0.0

    def test_none_values_handled(self):
        item = {"spice_level": None, "sweetness": None}
        vec = encode_food_item(item)
        assert vec[0] == 0.0
        assert vec[1] == 0.0


class TestEncodeContext:
    def test_output_dimension(self):
        ctx = encode_context()
        assert len(ctx) == CONTEXT_DIM

    def test_default_context(self):
        ctx = encode_context()
        # Context is [time_sin, time_cos, rejection, days]; defaults zero the tail.
        assert ctx[-2] == 0.0
        assert ctx[-1] == 0.0

    def test_time_encoding_cyclical(self):
        ctx_noon = encode_context(hour=12.0)
        ctx_midnight = encode_context(hour=0.0)
        # Different times should produce different sin/cos (time is at index 0/1)
        assert ctx_noon[0] != ctx_midnight[0] or ctx_noon[1] != ctx_midnight[1]

    def test_time_encoding_24h_wraps(self):
        ctx_0 = encode_context(hour=0.0)
        ctx_24 = encode_context(hour=24.0)
        # hour=0 and hour=24 should be same (cyclical)
        assert abs(ctx_0[0] - ctx_24[0]) < 1e-10
        assert abs(ctx_0[1] - ctx_24[1]) < 1e-10

    def test_rejection_rate_stored(self):
        ctx = encode_context(recent_rejection_rate=0.7)
        assert ctx[-2] == 0.7

    def test_days_since_stored(self):
        ctx = encode_context(days_since_last_session=3.0)
        assert ctx[-1] == 3.0


class TestBuildFeatureVector:
    def test_total_dimension(self):
        item = {"spice_level": 0.5, "protein_type": "chicken", "cuisine_type": "thai", "carb_base": "rice"}
        context = {"hour": 12.0}
        vec = build_feature_vector(item, context)
        assert len(vec) == TOTAL_DIM

    def test_food_and_context_concatenated(self):
        item = {"spice_level": 0.9}
        context = {"hour": 6.0}
        vec = build_feature_vector(item, context)
        # First element is spice_level
        assert vec[0] == 0.9
        # Total is food + context + interactions
        assert len(vec) == FOOD_DIM + CONTEXT_DIM + INTERACTION_DIM


class TestDimensionConsistency:
    def test_food_dim_matches(self):
        expected = len(CONTINUOUS_ATTRS) + len(PROTEIN_TYPES) + len(CUISINE_TYPES) + len(CARB_BASES)
        assert FOOD_DIM == expected

    def test_context_dim_matches(self):
        expected = 2 + 2  # time_sin/cos + rejection + days
        assert CONTEXT_DIM == expected

    def test_interaction_dim_matches_toggle(self):
        # INTERACTION_DIM is 0 when toggle off, else len(INTERACTION_TERMS)
        assert INTERACTION_DIM in (0, len(INTERACTION_TERMS))

    def test_total_dim_matches(self):
        assert TOTAL_DIM == FOOD_DIM + CONTEXT_DIM + INTERACTION_DIM


class TestEncodeInteractions:
    def test_output_dimension(self):
        item = {"spice_level": 0.8, "temperature": 0.9, "dairy_content": 0.5}
        ctx = {"hour": 19.0}
        vec = encode_interactions(item, ctx)
        # encode_interactions always returns full term length regardless of toggle
        assert len(vec) == len(INTERACTION_TERMS)

    def test_time_interaction_present(self):
        # temperature×time_sin (index 0) / time_cos (index 1)
        item = {"temperature": 1.0}
        ctx = {"hour": 6.0}
        vec = encode_interactions(item, ctx)
        # not zero (sin/cos at 6h are nonzero)
        assert vec[0] != 0.0 or vec[1] != 0.0


class TestFeatureSchema:
    def test_total_dim_no_interactions(self):
        schema = FeatureSchema(use_interactions=False)
        assert schema.total_dim == FOOD_DIM + CONTEXT_DIM

    def test_total_dim_with_interactions(self):
        schema = FeatureSchema(use_interactions=True)
        assert schema.total_dim == FOOD_DIM + CONTEXT_DIM + len(INTERACTION_TERMS)

    def test_food_dim(self):
        schema = FeatureSchema()
        assert schema.food_dim == FOOD_DIM

    def test_context_dim(self):
        schema = FeatureSchema()
        assert schema.context_dim == CONTEXT_DIM

    def test_validate_model_ok(self):
        from model.thompson import ThompsonSamplingModel, ModelConfig
        schema = FeatureSchema(use_interactions=False)
        model = ThompsonSamplingModel(ModelConfig(dim=schema.total_dim))
        assert schema.validate_model(model) is True

    def test_validate_model_dim_mismatch_returns_false(self):
        from model.thompson import ThompsonSamplingModel, ModelConfig
        schema = FeatureSchema(use_interactions=False)
        model = ThompsonSamplingModel(ModelConfig(dim=schema.total_dim + 8))  # wrong dim
        # Stale blob signals False (caller resets to fresh prior) rather than raising.
        assert schema.validate_model(model) is False


class TestEncodeFoodItemUnknownCategory:
    def test_unknown_cuisine_raises(self):
        with pytest.raises(ValueError, match="Unknown category"):
            encode_food_item({"cuisine_type": "martian"})

    def test_unknown_protein_raises(self):
        with pytest.raises(ValueError, match="Unknown category"):
            encode_food_item({"protein_type": "kangaroo"})
