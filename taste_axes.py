"""Taste Axes scoring — the one definition of the 5 Insights spectra.

A pure function over right-swiped item attribute rows. No DB, no I/O — the
single source of how a Taste Axis is computed, called once for the current
axes and once per Drift window by db.swipe_events.get_insights().

Decision (CONTEXT.md → "Taste Axes"): attribute-averaging over right swipes,
raw 0-100 scaling, NOT mu-projection or population-percentile normalization.

Each axis (0-100):
  Heat       = mean(spice_level)
  Indulgence = mean of mean(richness), mean(dairy_content), mean(sauce_heaviness)
  Texture    = 1 - mean(texture_softness)        (Smooth -> Crunchy)
  Adventure  = normalized Shannon entropy of the cuisine_type distribution
  Tempo      = fraction of right swipes in [18:00, 04:00)

NULL handling mirrors SQL AVG/GROUP BY exactly: each mean skips its own NULLs;
Adventure groups a NULL cuisine as its own bucket (SQLite GROUP BY semantics);
Tempo's denominator counts only rows with a non-NULL time_of_day.
"""

from __future__ import annotations

import math
from collections import Counter

AXIS_KEYS = ["Heat", "Indulgence", "Texture", "Adventure", "Tempo"]


def mean_attr(rows: list, key: str) -> float:
    """Mean of one attribute over rows, skipping NULLs — matches SQL AVG.

    Empty (or all-NULL) -> 0.0, mirroring SQL `AVG(...) or 0.0`. Shared by
    every right-swipe scorer (Taste Axes here, Profile Stats flavor_profile)
    so the NULL-skipping rule has one definition."""
    vals = [r[key] for r in rows if r[key] is not None]
    return sum(vals) / len(vals) if vals else 0.0


def taste_axes(rows: list) -> dict[str, int]:
    """Score the 5 Taste Axes (0-100 int each) over right-swiped item rows.

    Each row exposes: spice_level, richness, dairy_content, sauce_heaviness,
    texture_softness, cuisine_type, time_of_day. Accepts sqlite3.Row or dict.
    Empty rows -> all-zero axes (Texture 100, mirroring AVG(NULL) -> 0).
    """
    heat = round(mean_attr(rows, "spice_level") * 100)
    indulgence = round(
        (mean_attr(rows, "richness") + mean_attr(rows, "dairy_content")
         + mean_attr(rows, "sauce_heaviness")) / 3 * 100
    )
    texture = round((1 - mean_attr(rows, "texture_softness")) * 100)

    # Adventure: normalized Shannon entropy of the cuisine distribution.
    # NULL cuisine forms its own group, matching SQLite GROUP BY.
    counts = list(Counter(r["cuisine_type"] for r in rows).values())
    n_distinct = len(counts)
    c_total = sum(counts)
    if n_distinct > 1 and c_total > 0:
        entropy = -sum((c / c_total) * math.log(c / c_total) for c in counts)
        adventure = round((entropy / math.log(n_distinct)) * 100)
    else:
        adventure = 0

    # Tempo: fraction of right swipes (with a known time) in [18:00, 04:00).
    tods = [r["time_of_day"] for r in rows if r["time_of_day"] is not None]
    denom = len(tods)
    night = sum(1 for t in tods if t >= 18 or t < 4)
    tempo = round((night / denom) * 100) if denom > 0 else 0

    return {
        "Heat": heat,
        "Indulgence": indulgence,
        "Texture": texture,
        "Adventure": adventure,
        "Tempo": tempo,
    }
