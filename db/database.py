"""SQLite database initialization and access."""

import secrets
import sqlite3
from pathlib import Path

from tagging.safety import DIETARY_FLAGS, SAFETY_FLAGS

SCHEMA_PATH = Path(__file__).parent / "schema.sql"
DEFAULT_DB_PATH = Path(__file__).parent.parent / "cravings.db"


def generate_api_token() -> str:
    """Generate a URL-safe random API token (~32 chars)."""
    return secrets.token_urlsafe(24)


def insert_user(conn: sqlite3.Connection, name: str,
                dietary_flags_bitmask: int = 0,
                safety_overrides_bitmask: int = 0) -> tuple[int, str]:
    """Insert user, return (user_id, api_token)."""
    token = generate_api_token()
    cursor = conn.execute(
        "INSERT INTO users (name, api_token, dietary_flags_bitmask, safety_overrides_bitmask) "
        "VALUES (?, ?, ?, ?)",
        [name, token, dietary_flags_bitmask, safety_overrides_bitmask],
    )
    conn.commit()
    return cursor.lastrowid, token


def get_user_by_token(conn: sqlite3.Connection, token: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM users WHERE api_token = ?", [token]
    ).fetchone()
    return dict(row) if row else None


def get_user(conn: sqlite3.Connection, user_id: int) -> dict | None:
    row = conn.execute(
        "SELECT * FROM users WHERE id = ?", [user_id]
    ).fetchone()
    return dict(row) if row else None


def update_user_model_state(conn: sqlite3.Connection, user_id: int,
                             mu_blob: bytes, b_blob: bytes,
                             total_swipes: int, last_decay_ts: float,
                             drift_active: bool) -> None:
    conn.execute(
        "UPDATE users SET mu_blob = ?, b_blob = ?, total_swipes = ?, "
        "last_decay_ts = ?, drift_active = ?, updated_at = CURRENT_TIMESTAMP "
        "WHERE id = ?",
        [mu_blob, b_blob, total_swipes, last_decay_ts, int(drift_active), user_id],
    )
    conn.commit()


def update_user_onboarding(conn: sqlite3.Connection, user_id: int,
                           dietary_flags_bitmask: int,
                           safety_overrides_bitmask: int) -> None:
    conn.execute(
        "UPDATE users SET dietary_flags_bitmask = ?, safety_overrides_bitmask = ?, "
        "onboarding_complete = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        [dietary_flags_bitmask, safety_overrides_bitmask, user_id],
    )
    conn.commit()


def get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = get_connection(db_path)
    schema_sql = SCHEMA_PATH.read_text()
    conn.executescript(schema_sql)
    _migrate(conn)
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    """Idempotent column adds for existing databases."""
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(swipe_events)").fetchall()}
    if "recent_rejection_rate" not in cols:
        conn.execute("ALTER TABLE swipe_events ADD COLUMN recent_rejection_rate REAL NOT NULL DEFAULT 0.0")
    if "days_since_last_session" not in cols:
        conn.execute("ALTER TABLE swipe_events ADD COLUMN days_since_last_session REAL NOT NULL DEFAULT 0.0")
    conn.commit()


def insert_food_item(conn: sqlite3.Connection, item: dict) -> int:
    cols = [
        "name", "description", "restaurant_id",
        "spice_level", "sweetness", "sourness", "savory_umami", "saltiness", "bitterness",
        "temperature", "texture_softness", "sauce_heaviness", "richness",
        "protein_type", "cuisine_type", "carb_base", "veggie_density", "dairy_content",
        "smell_intensity", "nausea_trigger",
        "safety_risk_bitmask", "dietary_flags_bitmask", "tagging_status",
    ]
    present = {k: v for k, v in item.items() if k in cols}
    col_names = ", ".join(present.keys())
    placeholders = ", ".join(["?"] * len(present))
    cursor = conn.execute(
        f"INSERT INTO food_items ({col_names}) VALUES ({placeholders})",
        list(present.values()),
    )
    conn.commit()
    return cursor.lastrowid


def insert_restaurant(conn: sqlite3.Connection, restaurant: dict) -> int:
    cols = ["name", "location", "cuisine_type", "source_type"]
    present = {k: v for k, v in restaurant.items() if k in cols}
    col_names = ", ".join(present.keys())
    placeholders = ", ".join(["?"] * len(present))
    cursor = conn.execute(
        f"INSERT INTO restaurants ({col_names}) VALUES ({placeholders})",
        list(present.values()),
    )
    conn.commit()
    return cursor.lastrowid


def get_untagged_items(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT id, name, description FROM food_items WHERE tagging_status = 'pending'"
    ).fetchall()
    return [dict(r) for r in rows]


def get_eligible_food_items(
    conn: sqlite3.Connection,
    safety_mask: int,
    dietary_restrictions: list[str],
    exclude_ids: list[int] | None = None,
) -> list[dict]:
    clauses = ["tagging_status = 'tagged'", "(safety_risk_bitmask & ?) = 0"]
    args: list = [safety_mask]

    for r in (dietary_restrictions or []):
        bit = DIETARY_FLAGS.get(r)
        if bit is None:
            continue
        mask = 1 << bit
        if r.startswith("contains_"):
            clauses.append("(dietary_flags_bitmask & ?) = 0")
        else:
            clauses.append("(dietary_flags_bitmask & ?) != 0")
        args.append(mask)

    if exclude_ids:
        placeholders = ",".join("?" * len(exclude_ids))
        clauses.append(f"id NOT IN ({placeholders})")
        args.extend(exclude_ids)

    query = (
        "SELECT id, name, description, restaurant_id, "
        "spice_level, sweetness, sourness, savory_umami, saltiness, bitterness, "
        "temperature, texture_softness, sauce_heaviness, richness, "
        "protein_type, cuisine_type, carb_base, veggie_density, dairy_content, "
        "smell_intensity, nausea_trigger, "
        "safety_risk_bitmask, dietary_flags_bitmask, tagging_status "
        "FROM food_items WHERE " + " AND ".join(clauses)
    )
    rows = conn.execute(query, args).fetchall()
    return [dict(r) for r in rows]


def get_food_item(conn: sqlite3.Connection, item_id: int) -> dict | None:
    row = conn.execute(
        "SELECT id, name, description, restaurant_id, "
        "spice_level, sweetness, sourness, savory_umami, saltiness, bitterness, "
        "temperature, texture_softness, sauce_heaviness, richness, "
        "protein_type, cuisine_type, carb_base, veggie_density, dairy_content, "
        "smell_intensity, nausea_trigger, "
        "safety_risk_bitmask, dietary_flags_bitmask, tagging_status "
        "FROM food_items WHERE id = ?",
        [item_id],
    ).fetchone()
    return dict(row) if row else None


def list_food_items(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT id, name, description, restaurant_id, "
        "spice_level, sweetness, sourness, savory_umami, saltiness, bitterness, "
        "temperature, texture_softness, sauce_heaviness, richness, "
        "protein_type, cuisine_type, carb_base, veggie_density, dairy_content, "
        "smell_intensity, nausea_trigger, "
        "safety_risk_bitmask, dietary_flags_bitmask, tagging_status "
        "FROM food_items WHERE tagging_status = 'tagged'"
    ).fetchall()
    return [dict(r) for r in rows]


def list_restaurants(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT id, name, COALESCE(location, '') as location, "
        "COALESCE(cuisine_type, '') as cuisine_type, source_type FROM restaurants"
    ).fetchall()
    return [dict(r) for r in rows]


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


def mark_onboarding_complete(conn: sqlite3.Connection, user_id: int) -> None:
    conn.execute(
        "UPDATE users SET onboarding_complete = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        [user_id],
    )
    conn.commit()


def update_food_item_tags(conn: sqlite3.Connection, item_id: int, tags: dict) -> None:
    tag_cols = [
        "spice_level", "sweetness", "sourness", "savory_umami", "saltiness", "bitterness",
        "temperature", "texture_softness", "sauce_heaviness", "richness",
        "protein_type", "cuisine_type", "carb_base", "veggie_density", "dairy_content",
        "smell_intensity", "nausea_trigger",
        "safety_risk_bitmask", "dietary_flags_bitmask",
    ]
    present = {k: v for k, v in tags.items() if k in tag_cols}
    present["tagging_status"] = "tagged"
    set_clause = ", ".join(f"{k} = ?" for k in present.keys())
    conn.execute(
        f"UPDATE food_items SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        [*present.values(), item_id],
    )
    conn.commit()
