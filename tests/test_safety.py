"""Tests for safety and dietary flag bitmask logic."""

import pytest

from tagging.safety import (
    compute_safety_bitmask,
    compute_dietary_bitmask,
    has_safety_flag,
    has_dietary_flag,
)


class TestSafetyBitmask:
    def test_empty_flags(self):
        assert compute_safety_bitmask([]) == 0

    def test_single_flag(self):
        mask = compute_safety_bitmask(["raw_fish"])
        assert mask == 1  # bit 0

    def test_multiple_flags(self):
        mask = compute_safety_bitmask(["raw_fish", "raw_meat"])
        assert mask == 0b00101  # bits 0 and 2

    def test_all_flags(self):
        all_flags = ["raw_fish", "raw_egg", "raw_meat", "unpasteurized_dairy", "high_mercury_fish"]
        mask = compute_safety_bitmask(all_flags)
        assert mask == 0b11111

    def test_invalid_flag_ignored(self):
        mask = compute_safety_bitmask(["raw_fish", "not_a_real_flag"])
        assert mask == 1

    def test_has_safety_flag(self):
        mask = compute_safety_bitmask(["raw_fish", "high_mercury_fish"])
        assert has_safety_flag(mask, "raw_fish")
        assert has_safety_flag(mask, "high_mercury_fish")
        assert not has_safety_flag(mask, "raw_egg")


class TestDietaryBitmask:
    def test_empty_flags(self):
        assert compute_dietary_bitmask([]) == 0

    def test_vegetarian(self):
        mask = compute_dietary_bitmask(["vegetarian"])
        assert mask == 1  # bit 0

    def test_multiple_flags(self):
        mask = compute_dietary_bitmask(["vegetarian", "gluten_free"])
        assert mask == 0b0101  # bits 0 and 2

    def test_allergen_flags(self):
        mask = compute_dietary_bitmask(["contains_nuts", "contains_shellfish"])
        assert has_dietary_flag(mask, "contains_nuts")
        assert has_dietary_flag(mask, "contains_shellfish")
        assert not has_dietary_flag(mask, "contains_soy")


class TestBitmaskSync:
    """Canonical bit positions — must match backend/store/store.go:safetyFlagBits and dietaryFlagBits.

    If these tests fail, update store.go to match. Python is the source of truth for bit assignments.
    """

    def test_safety_bit_positions(self):
        assert compute_safety_bitmask(["raw_fish"]) == 1           # bit 0
        assert compute_safety_bitmask(["raw_egg"]) == 2            # bit 1
        assert compute_safety_bitmask(["raw_meat"]) == 4           # bit 2
        assert compute_safety_bitmask(["unpasteurized_dairy"]) == 8  # bit 3
        assert compute_safety_bitmask(["high_mercury_fish"]) == 16   # bit 4

    def test_dietary_bit_positions(self):
        assert compute_dietary_bitmask(["vegetarian"]) == 1        # bit 0
        assert compute_dietary_bitmask(["vegan"]) == 2             # bit 1
        assert compute_dietary_bitmask(["gluten_free"]) == 4       # bit 2
        assert compute_dietary_bitmask(["dairy_free"]) == 8        # bit 3
        assert compute_dietary_bitmask(["halal"]) == 16            # bit 4
        assert compute_dietary_bitmask(["kosher"]) == 32           # bit 5
        assert compute_dietary_bitmask(["contains_nuts"]) == 64    # bit 6
        assert compute_dietary_bitmask(["contains_shellfish"]) == 128  # bit 7
        assert compute_dietary_bitmask(["contains_soy"]) == 256    # bit 8
        assert compute_dietary_bitmask(["contains_eggs"]) == 512   # bit 9
