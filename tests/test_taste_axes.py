"""Pure unit tests for the Taste Axes seam — no DB, no I/O.

This is the payoff of extracting taste_axes() out of get_insights(): the axis
math (mean, 1-x, normalized entropy, night-fraction) is now testable on plain
dicts. The DB-backed end-to-end behavior is still covered by test_insights.py.
"""

import math

from taste_axes import AXIS_KEYS, mean_attr, taste_axes


def _row(spice=0.0, richness=0.0, dairy=0.0, sauce=0.0, texture=0.0,
         cuisine="japanese", tod=12.0):
    return {
        "spice_level": spice, "richness": richness, "dairy_content": dairy,
        "sauce_heaviness": sauce, "texture_softness": texture,
        "cuisine_type": cuisine, "time_of_day": tod,
    }


def test_mean_attr_skips_nulls():
    assert mean_attr([{"x": 0.8}, {"x": None}, {"x": 0.2}], "x") == 0.5


def test_mean_attr_empty_is_zero():
    assert mean_attr([], "x") == 0.0
    assert mean_attr([{"x": None}], "x") == 0.0


def test_empty_rows_all_zero_except_texture():
    # AVG over no rows is NULL -> 0; Texture = 1 - 0 = 100 (mirrors SQL `or 0.0`).
    axes = taste_axes([])
    assert axes == {"Heat": 0, "Indulgence": 0, "Texture": 100,
                    "Adventure": 0, "Tempo": 0}


def test_heat_is_mean_spice():
    axes = taste_axes([_row(spice=0.8), _row(spice=0.2)])
    assert axes["Heat"] == 50  # mean(0.8, 0.2) * 100


def test_indulgence_is_mean_of_three_means():
    axes = taste_axes([_row(richness=0.6, dairy=0.3, sauce=0.9)])
    assert axes["Indulgence"] == round((0.6 + 0.3 + 0.9) / 3 * 100)


def test_texture_inverts_softness():
    axes = taste_axes([_row(texture=0.2)])
    assert axes["Texture"] == 80  # 1 - 0.2


def test_adventure_single_cuisine_is_zero():
    axes = taste_axes([_row(cuisine="japanese"), _row(cuisine="japanese")])
    assert axes["Adventure"] == 0  # entropy 0 with one bucket


def test_adventure_equal_split_is_max():
    axes = taste_axes([_row(cuisine="japanese"), _row(cuisine="italian")])
    assert axes["Adventure"] == 100  # normalized entropy = 1.0


def test_adventure_null_cuisine_is_own_bucket():
    # SQLite GROUP BY groups NULL as one bucket; two distinct buckets -> entropy.
    axes = taste_axes([_row(cuisine=None), _row(cuisine="italian")])
    assert axes["Adventure"] == 100


def test_tempo_night_window_inclusive_and_exclusive():
    assert taste_axes([_row(tod=20.0)])["Tempo"] == 100   # 18:00 in window
    assert taste_axes([_row(tod=3.0)])["Tempo"] == 100    # before 04:00 in window
    assert taste_axes([_row(tod=12.0)])["Tempo"] == 0     # noon out
    assert taste_axes([_row(tod=4.0)])["Tempo"] == 0      # 04:00 exclusive boundary


def test_tempo_ignores_null_time_in_denominator():
    # One night row + one unknown-time row -> denom counts only the timed row.
    axes = taste_axes([_row(tod=20.0), _row(tod=None)])
    assert axes["Tempo"] == 100


def test_means_skip_per_attribute_nulls():
    # Matches SQL AVG: each attribute averages only its non-NULL values.
    axes = taste_axes([_row(spice=0.4), _row(spice=None)])
    assert axes["Heat"] == 40  # mean over the single non-null spice


def test_accepts_sqlite_row_like_mapping():
    # taste_axes indexes rows by key; any mapping works.
    axes = taste_axes([_row(spice=1.0)])
    assert set(axes) == set(AXIS_KEYS)


def test_adventure_matches_manual_entropy_formula():
    # 3:1 split across two cuisines — guards the normalization denominator.
    rows = [_row(cuisine="japanese")] * 3 + [_row(cuisine="italian")]
    counts = [3, 1]
    total = 4
    entropy = -sum((c / total) * math.log(c / total) for c in counts)
    expected = round((entropy / math.log(2)) * 100)
    assert taste_axes(rows)["Adventure"] == expected
