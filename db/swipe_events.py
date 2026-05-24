"""Swipe event recording, stats aggregation, and cuisine history."""

import sqlite3


def record_swipe(
    conn: sqlite3.Connection,
    user_id: int,
    food_item_id: int,
    direction: str,
    dietary_mode: str,
    time_of_day: float,
    mood: str,
    recent_rejection_rate: float,
    days_since_last_session: float,
) -> None:
    conn.execute(
        "INSERT INTO swipe_events "
        "(user_id, food_item_id, direction, dietary_mode, time_of_day, mood, "
        " recent_rejection_rate, days_since_last_session) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [user_id, food_item_id, direction, dietary_mode, time_of_day, mood,
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

    # Mood breakdown
    mood_rows = conn.execute(
        "SELECT mood, direction, COUNT(*) AS n FROM swipe_events "
        "WHERE user_id = ? GROUP BY mood, direction",
        [user_id],
    ).fetchall()
    mood_map: dict[str, dict] = {}
    for r in mood_rows:
        m = r["mood"] or "no_preference"
        if m not in mood_map:
            mood_map[m] = {"mood": m, "right": 0, "left": 0}
        mood_map[m][r["direction"]] = r["n"]
    mood_breakdown = list(mood_map.values())

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

    # Totals from users row
    user_row = conn.execute(
        "SELECT total_swipes, drift_active FROM users WHERE id = ?", [user_id]
    ).fetchone()

    return {
        "total_swipes": user_row["total_swipes"] if user_row else 0,
        "drift_active": bool(user_row["drift_active"]) if user_row else False,
        "cuisine_breakdown": cuisine_breakdown,
        "avg_swipes_to_right": avg_swipes_to_right,
        "mood_breakdown": mood_breakdown,
        "hour_breakdown": hour_breakdown,
    }
