"""Cross-user admin metrics — org-wide aggregates over swipe_events + users.

Distinct from per-user db.swipe_events (Insights / Profile Stats, premium-gated):
these read across ALL users for the admin dashboard. Caveats baked into outputs:

  * Registered users only — guests have no DB rows (ADR-0005).
  * "Active" = swiped that day. No app-open / session / login events exist yet;
    closing that gap is the P2 instrumentation work.

Raw parameterized SQL, computed on-the-fly (current scale doesn't need caching).
Aggregates only — no per-user PII (emails / identities) leaves these functions.
"""

import sqlite3

from taste_axes import mean_attr

# Columns safe to GROUP BY in catalog_trends (whitelist — never interpolate user input).
_CATALOG_DIMENSIONS = ("cuisine_type", "protein_type", "carb_base")

# Attributes summarised as org-wide means over right swipes.
_RIGHT_ATTRS = (
    "spice_level", "richness", "dairy_content", "sauce_heaviness",
    "texture_softness", "savory_umami", "veggie_density", "sweetness",
)


def _rate(right: int, total: int) -> int:
    """Right-swipe rate as a 0-100 int, matching say_yes_rate convention."""
    return round((right / total) * 100) if total else 0


def food_performance(
    conn: sqlite3.Connection,
    min_swipes: int = 5,
    limit: int = 20,
    cuisine: str | None = None,
) -> dict:
    """Per-food right/left/never counts + rates, ranked best & worst.

    `min_swipes` suppresses low-sample noise (a 1/1 food isn't "the best").
    Impressions (times shown) come from user_item_impressions for an
    impression-adjusted popularity view.
    """
    sql = (
        "SELECT fi.id AS food_id, fi.name, fi.cuisine_type, r.name AS restaurant, "
        "SUM(CASE WHEN se.direction='right' THEN 1 ELSE 0 END) AS rights, "
        "SUM(CASE WHEN se.direction='left'  THEN 1 ELSE 0 END) AS lefts, "
        "SUM(CASE WHEN se.direction='never' THEN 1 ELSE 0 END) AS nevers, "
        "COUNT(*) AS total, "
        "COALESCE(imp.shown, 0) AS impressions "
        "FROM swipe_events se "
        "JOIN food_items fi ON fi.id = se.food_item_id "
        "LEFT JOIN restaurants r ON r.id = fi.restaurant_id "
        "LEFT JOIN (SELECT food_item_id, SUM(count) AS shown "
        "           FROM user_item_impressions GROUP BY food_item_id) imp "
        "  ON imp.food_item_id = fi.id "
    )
    params: list = []
    if cuisine:
        sql += "WHERE fi.cuisine_type = ? "
        params.append(cuisine)
    sql += "GROUP BY fi.id HAVING total >= ?"
    params.append(min_swipes)

    rows = conn.execute(sql, params).fetchall()
    foods = []
    for r in rows:
        total = r["total"]
        foods.append({
            "food_id": r["food_id"],
            "name": r["name"],
            "cuisine_type": r["cuisine_type"],
            "restaurant": r["restaurant"],
            "right": r["rights"],
            "left": r["lefts"],
            "never": r["nevers"],
            "total": total,
            "right_rate": _rate(r["rights"], total),
            "impressions": r["impressions"],
        })

    by_rate = sorted(foods, key=lambda f: (f["right_rate"], f["total"]), reverse=True)
    return {
        "min_swipes": min_swipes,
        "food_count": len(foods),
        "best": by_rate[:limit],
        "worst": list(reversed(by_rate[-limit:])) if foods else [],
    }


def _dimension_rates(conn: sqlite3.Connection, column: str) -> list[dict]:
    """Right-rate grouped by one catalog column (column must be whitelisted)."""
    if column not in _CATALOG_DIMENSIONS:
        raise ValueError(f"non-whitelisted dimension: {column}")
    rows = conn.execute(
        f"SELECT fi.{column} AS k, "
        "SUM(CASE WHEN se.direction='right' THEN 1 ELSE 0 END) AS rights, "
        "COUNT(*) AS total "
        "FROM swipe_events se JOIN food_items fi ON fi.id = se.food_item_id "
        f"GROUP BY fi.{column}"
    ).fetchall()
    out = [
        {"key": r["k"] or "unknown", "right": r["rights"],
         "total": r["total"], "right_rate": _rate(r["rights"], r["total"])}
        for r in rows
    ]
    return sorted(out, key=lambda d: d["right_rate"], reverse=True)


def catalog_trends(conn: sqlite3.Connection) -> dict:
    """Right-rate by cuisine/protein/carb + org-wide mean attrs of right swipes."""
    attr_rows = conn.execute(
        "SELECT " + ", ".join(f"f.{a}" for a in _RIGHT_ATTRS) + " "
        "FROM swipe_events se JOIN food_items f ON f.id = se.food_item_id "
        "WHERE se.direction = 'right'"
    ).fetchall()
    attributes = {a: round(mean_attr(attr_rows, a) * 100) for a in _RIGHT_ATTRS}

    return {
        "by_cuisine": _dimension_rates(conn, "cuisine_type"),
        "by_protein": _dimension_rates(conn, "protein_type"),
        "by_carb": _dimension_rates(conn, "carb_base"),
        "right_swipe_attributes": attributes,
    }


def retention(conn: sqlite3.Connection, days: int = 30, cohort_days: list[int] | None = None) -> dict:
    """Activity (DAU/WAU/MAU) + signups + N-day cohort retention.

    Active = has a swipe that day. Population = registered users only.
    Cohort DN retention = fraction of users old enough to reach day N who were
    active exactly on the Nth day after signup.
    """
    cohort_days = cohort_days or [1, 7, 30]

    def _active_since(window: str) -> int:
        row = conn.execute(
            "SELECT COUNT(DISTINCT user_id) AS n FROM swipe_events "
            "WHERE timestamp >= datetime('now', ?)",
            [window],
        ).fetchone()
        return row["n"] if row else 0

    signups = conn.execute(
        "SELECT date(created_at) AS day, COUNT(*) AS n FROM users "
        "WHERE email IS NOT NULL AND created_at >= datetime('now', ?) "
        "GROUP BY day ORDER BY day",
        [f"-{days} days"],
    ).fetchall()

    cohort_retention: dict[str, int] = {}
    cohort_eligible: dict[str, int] = {}
    for n in cohort_days:
        elig_row = conn.execute(
            "SELECT COUNT(*) AS n FROM users "
            "WHERE email IS NOT NULL AND julianday('now') - julianday(created_at) >= ?",
            [n],
        ).fetchone()
        eligible = elig_row["n"] if elig_row else 0
        ret_row = conn.execute(
            "SELECT COUNT(DISTINCT u.id) AS n FROM users u "
            "JOIN swipe_events se ON se.user_id = u.id "
            "WHERE u.email IS NOT NULL "
            "  AND julianday('now') - julianday(u.created_at) >= ? "
            "  AND CAST(julianday(se.timestamp) - julianday(u.created_at) AS INTEGER) = ?",
            [n, n],
        ).fetchone()
        retained = ret_row["n"] if ret_row else 0
        cohort_eligible[f"D{n}"] = eligible
        cohort_retention[f"D{n}"] = round((retained / eligible) * 100) if eligible else 0

    return {
        "active_definition": "swiped",
        "population": "registered_only",
        "dau": _active_since("-1 days"),
        "wau": _active_since("-7 days"),
        "mau": _active_since("-30 days"),
        "signups": [dict(r) for r in signups],
        "cohort_retention": cohort_retention,
        "cohort_eligible": cohort_eligible,
    }


def engagement(conn: sqlite3.Connection, days: int = 30) -> dict:
    """Swipe volume over time, per-user distribution, say-yes trend, conversions."""
    per_day = conn.execute(
        "SELECT date(timestamp) AS day, COUNT(*) AS n, "
        "SUM(CASE WHEN direction='right' THEN 1 ELSE 0 END) AS rights "
        "FROM swipe_events WHERE timestamp >= datetime('now', ?) "
        "GROUP BY day ORDER BY day",
        [f"-{days} days"],
    ).fetchall()
    swipes_per_day = [
        {"day": r["day"], "n": r["n"], "right": r["rights"],
         "say_yes_rate": _rate(r["rights"], r["n"])}
        for r in per_day
    ]

    # Per-user swipe-count distribution → fixed buckets.
    counts = conn.execute(
        "SELECT user_id, COUNT(*) AS n FROM swipe_events GROUP BY user_id"
    ).fetchall()
    buckets = [("1-9", 1, 9), ("10-49", 10, 49), ("50-99", 50, 99),
               ("100-499", 100, 499), ("500+", 500, None)]
    histogram = []
    for label, lo, hi in buckets:
        users = sum(1 for c in counts if c["n"] >= lo and (hi is None or c["n"] <= hi))
        histogram.append({"bucket": label, "users": users})

    totals = conn.execute(
        "SELECT COUNT(*) AS total, "
        "SUM(CASE WHEN direction='right' THEN 1 ELSE 0 END) AS rights "
        "FROM swipe_events"
    ).fetchone()
    total_swipes = totals["total"] if totals else 0
    global_say_yes = _rate(totals["rights"] or 0, total_swipes) if totals else 0

    user_row = conn.execute(
        "SELECT COUNT(*) AS total, "
        "SUM(CASE WHEN is_premium=1 THEN 1 ELSE 0 END) AS premium "
        "FROM users WHERE email IS NOT NULL"
    ).fetchone()
    conv_row = conn.execute(
        "SELECT COUNT(*) AS n FROM billing_sessions "
        "WHERE status = 'completed' AND completed_at >= datetime('now', ?)",
        [f"-{days} days"],
    ).fetchone()

    return {
        "total_swipes": total_swipes,
        "global_say_yes_rate": global_say_yes,
        "swipes_per_day": swipes_per_day,
        "swipes_per_user_histogram": histogram,
        "active_users_with_swipes": len(counts),
        "registered_users": user_row["total"] if user_row else 0,
        "premium_users": (user_row["premium"] or 0) if user_row else 0,
        "premium_conversions_recent": conv_row["n"] if conv_row else 0,
    }
