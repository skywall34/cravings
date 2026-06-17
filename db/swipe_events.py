"""Swipe event recording, stats aggregation, and cuisine history."""

import sqlite3

from taste_axes import AXIS_KEYS, mean_attr, taste_axes


def record_swipe(
    conn: sqlite3.Connection,
    user_id: int,
    food_item_id: int,
    direction: str,
    time_of_day: float,
    recent_rejection_rate: float,
    days_since_last_session: float,
) -> None:
    # dietary_mode / mood columns are deprecated (no longer written) — left NULL.
    conn.execute(
        "INSERT INTO swipe_events "
        "(user_id, food_item_id, direction, time_of_day, "
        " recent_rejection_rate, days_since_last_session) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [user_id, food_item_id, direction, time_of_day,
         recent_rejection_rate, days_since_last_session],
    )
    conn.commit()


def recent_rejection_rate(conn: sqlite3.Connection, user_id: int, n: int = 10) -> float:
    rows = conn.execute(
        "SELECT direction FROM swipe_events WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        [user_id, n],
    ).fetchall()
    if not rows:
        return 0.0
    lefts = sum(1 for r in rows if r["direction"] == "left")
    return lefts / len(rows)


def days_since_last_swipe(conn: sqlite3.Connection, user_id: int) -> float:
    row = conn.execute(
        "SELECT (julianday('now') - julianday(MAX(timestamp))) * 86400.0 as seconds "
        "FROM swipe_events WHERE user_id = ?",
        [user_id],
    ).fetchone()
    if row is None or row["seconds"] is None:
        return 0.0
    return row["seconds"] / 86400.0


def get_swiped_cuisines(conn: sqlite3.Connection, user_id: int) -> set[str]:
    """Return cuisine types the user has swiped on (excludes 'other'). Used for stratified cold-start."""
    rows = conn.execute(
        "SELECT DISTINCT f.cuisine_type FROM swipe_events se "
        "JOIN food_items f ON se.food_item_id = f.id WHERE se.user_id = ?",
        [user_id],
    ).fetchall()
    return {r[0] for r in rows if r[0] and r[0] != "other"}


def get_swipe_stats(conn: sqlite3.Connection, user_id: int) -> dict:
    # Cuisine breakdown by direction
    cuisine_rows = conn.execute(
        "SELECT f.cuisine_type, se.direction, COUNT(*) AS n "
        "FROM swipe_events se JOIN food_items f ON se.food_item_id = f.id "
        "WHERE se.user_id = ? GROUP BY f.cuisine_type, se.direction ORDER BY n DESC",
        [user_id],
    ).fetchall()
    cuisine_map: dict[str, dict] = {}
    for r in cuisine_rows:
        c = r["cuisine_type"] or "other"
        if c not in cuisine_map:
            cuisine_map[c] = {"cuisine": c, "right": 0, "left": 0}
        cuisine_map[c][r["direction"]] = r["n"]
    cuisine_breakdown = sorted(
        cuisine_map.values(), key=lambda x: x["right"] + x["left"], reverse=True
    )

    # Avg swipes to right (compute in Python: runs of lefts before each right)
    events = conn.execute(
        "SELECT direction FROM swipe_events WHERE user_id = ? ORDER BY timestamp ASC",
        [user_id],
    ).fetchall()
    runs: list[int] = []
    lefts = 0
    for e in events:
        if e["direction"] == "left":
            lefts += 1
        else:
            runs.append(lefts)
            lefts = 0
    avg_swipes_to_right = round(sum(runs) / len(runs), 1) if runs else None

    # Hour-of-day breakdown
    hour_rows = conn.execute(
        "SELECT CAST(time_of_day AS INTEGER) AS hour, direction, COUNT(*) AS n "
        "FROM swipe_events WHERE user_id = ? AND time_of_day IS NOT NULL "
        "GROUP BY hour, direction ORDER BY hour",
        [user_id],
    ).fetchall()
    hour_map: dict[int, dict] = {}
    for r in hour_rows:
        h = r["hour"]
        if h not in hour_map:
            hour_map[h] = {"hour": h, "right": 0, "left": 0}
        hour_map[h][r["direction"]] = r["n"]
    hour_breakdown = sorted(hour_map.values(), key=lambda x: x["hour"])

    # Flavor profile (mean flavor axes over right-swiped dishes) — shares the
    # right-swipe reader + mean_attr with the Taste Axes seam, distinct scoring.
    fp_rows = _right_swiped_attribute_rows(conn, user_id)
    flavor_profile = {
        "Spicy": round(mean_attr(fp_rows, "spice_level") * 100),
        "Rich": round(mean_attr(fp_rows, "richness") * 100),
        "Umami": round(mean_attr(fp_rows, "savory_umami") * 100),
        "Fresh": round(mean_attr(fp_rows, "veggie_density") * 100),
        "Sweet": round(mean_attr(fp_rows, "sweetness") * 100),
    }

    # Lifetime count from swipe_events (survives taste resets); drift from users row
    lifetime_row = conn.execute(
        "SELECT COUNT(*) AS n FROM swipe_events WHERE user_id = ?", [user_id]
    ).fetchone()
    user_row = conn.execute(
        "SELECT drift_active FROM users WHERE id = ?", [user_id]
    ).fetchone()

    return {
        "total_swipes": lifetime_row["n"] if lifetime_row else 0,
        "drift_active": bool(user_row["drift_active"]) if user_row else False,
        "cuisine_breakdown": cuisine_breakdown,
        "avg_swipes_to_right": avg_swipes_to_right,
        "hour_breakdown": hour_breakdown,
        "flavor_profile": flavor_profile,
    }


def _right_swiped_attribute_rows(
    conn: sqlite3.Connection, user_id: int, before: str | None = None
) -> list:
    """Right-swiped item attribute rows for a user, optionally cumulative-to-date.

    The single 'which swipes feed a Taste Axis' query: right swipes only,
    joined to their food attributes. `before` (a timestamp string) bounds the
    cumulative Drift window (se.timestamp < before)."""
    sql = (
        "SELECT f.spice_level, f.richness, f.dairy_content, f.sauce_heaviness, "
        "f.texture_softness, f.savory_umami, f.veggie_density, f.sweetness, "
        "f.cuisine_type, se.time_of_day "
        "FROM swipe_events se JOIN food_items f ON se.food_item_id = f.id "
        "WHERE se.user_id = ? AND se.direction = 'right'"
    )
    params: list = [user_id]
    if before is not None:
        sql += " AND se.timestamp < ?"
        params.append(before)
    return conn.execute(sql, params).fetchall()


def get_insights(conn: sqlite3.Connection, user_id: int) -> dict:
    right_row = conn.execute(
        "SELECT COUNT(*) AS n FROM swipe_events WHERE user_id = ? AND direction = 'right'",
        [user_id],
    ).fetchone()
    total_right = right_row["n"] if right_row else 0
    ready = total_right >= 20

    total_row = conn.execute(
        "SELECT COUNT(*) AS n FROM swipe_events WHERE user_id = ?", [user_id]
    ).fetchone()
    total_all = total_row["n"] if total_row else 0

    if total_right == 0:
        return {
            "axes": {"Heat": 0, "Indulgence": 0, "Texture": 0, "Adventure": 0, "Tempo": 0},
            "drift": None,
            "recap": {"top_cuisine": None, "top_cuisines": [], "say_yes_rate": 0, "biggest_mover": None},
            "ready": ready,
            "total_right_swipes": total_right,
        }

    # Current axes: one read, scored by the shared Taste Axes seam.
    axes = taste_axes(_right_swiped_attribute_rows(conn, user_id))

    # Recap
    top_cuisine_row = conn.execute(
        "SELECT f.cuisine_type, COUNT(*) AS n FROM swipe_events se "
        "JOIN food_items f ON se.food_item_id = f.id "
        "WHERE se.user_id = ? AND se.direction = 'right' "
        "GROUP BY f.cuisine_type ORDER BY n DESC LIMIT 1",
        [user_id],
    ).fetchone()
    top_cuisine = top_cuisine_row["cuisine_type"] if top_cuisine_row else None

    top_cuisines_rows = conn.execute(
        "SELECT f.cuisine_type, COUNT(*) AS n FROM swipe_events se "
        "JOIN food_items f ON se.food_item_id = f.id "
        "WHERE se.user_id = ? AND se.direction = 'right' "
        "GROUP BY f.cuisine_type ORDER BY n DESC LIMIT 5",
        [user_id],
    ).fetchall()
    top_cuisines = [r["cuisine_type"] for r in top_cuisines_rows if r["cuisine_type"]]

    say_yes_rate = round((total_right / total_all) * 100) if total_all > 0 else 0
    recap: dict = {"top_cuisine": top_cuisine, "top_cuisines": top_cuisines, "say_yes_rate": say_yes_rate, "biggest_mover": None}

    # Drift: last 4 calendar months with right swipes, cumulative-to-date windows
    month_rows = conn.execute(
        "SELECT DISTINCT strftime('%Y-%m', timestamp) AS ym "
        "FROM swipe_events WHERE user_id = ? AND direction = 'right' "
        "ORDER BY ym DESC LIMIT 4",
        [user_id],
    ).fetchall()
    months = [r["ym"] for r in month_rows][::-1]  # chronological

    drift = None
    if len(months) >= 2:
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        series: dict[str, list] = {k: [] for k in AXIS_KEYS}
        windows = []

        for ym in months:
            year, mon = int(ym[:4]), int(ym[5:7])
            next_mon, next_year = (1, year + 1) if mon == 12 else (mon + 1, year)
            end_date = f"{next_year}-{next_mon:02d}-01"

            # Cumulative-to-date: same Taste Axes seam, bounded by end_date.
            w_axes = taste_axes(_right_swiped_attribute_rows(conn, user_id, before=end_date))

            windows.append(month_names[mon - 1])
            for k in AXIS_KEYS:
                series[k].append(w_axes[k])

        drift = {"windows": windows, "series": series}
        if len(windows) >= 2:
            recap["biggest_mover"] = max(AXIS_KEYS, key=lambda k: abs(series[k][-1] - series[k][0]))

    return {
        "axes": axes,
        "drift": drift,
        "recap": recap,
        "ready": ready,
        "total_right_swipes": total_right,
    }


def delete_swipes_for_user(conn: sqlite3.Connection, user_id: int) -> None:
    conn.execute("DELETE FROM swipe_events WHERE user_id = ?", [user_id])


def delete_impressions_for_user(conn: sqlite3.Connection, user_id: int) -> None:
    conn.execute("DELETE FROM user_item_impressions WHERE user_id = ?", [user_id])


def get_all_swipes_for_user(conn: sqlite3.Connection, user_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT se.direction, se.timestamp, "
        "fi.name AS food_name, fi.cuisine_type "
        "FROM swipe_events se "
        "JOIN food_items fi ON fi.id = se.food_item_id "
        "WHERE se.user_id = ? ORDER BY se.timestamp",
        [user_id],
    ).fetchall()
    return [dict(r) for r in rows]
