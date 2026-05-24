"""SQLite database initialization and access."""

import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import bcrypt as _bcrypt

from tagging.safety import SAFETY_FLAGS, build_dietary_filter_clauses

_FOOD_ITEM_COLS = (
    "id, name, description, restaurant_id, "
    "spice_level, sweetness, sourness, savory_umami, saltiness, bitterness, "
    "temperature, texture_softness, sauce_heaviness, richness, "
    "protein_type, cuisine_type, carb_base, veggie_density, dairy_content, "
    "smell_intensity, nausea_trigger, "
    "safety_risk_bitmask, dietary_flags_bitmask, tagging_status, "
    "image_slug, image_hash, image_author, image_license, image_source_url, image_review_status"
)
_FOOD_ITEM_COLS_WITH_EMBEDDING = _FOOD_ITEM_COLS + ", embedding"

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


def update_user_dietary(conn: sqlite3.Connection, user_id: int,
                        dietary_flags_bitmask: int,
                        safety_overrides_bitmask: int) -> None:
    conn.execute(
        "UPDATE users SET dietary_flags_bitmask = ?, safety_overrides_bitmask = ?, "
        "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        [dietary_flags_bitmask, safety_overrides_bitmask, user_id],
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


@contextmanager
def db_connection(db_path: Path = DEFAULT_DB_PATH) -> Generator[sqlite3.Connection, None, None]:
    conn = get_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()


def init_db(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = get_connection(db_path)
    schema_sql = SCHEMA_PATH.read_text()
    conn.executescript(schema_sql)
    _migrate(conn)
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    """Idempotent column adds for existing databases."""
    swipe_cols = {r["name"] for r in conn.execute("PRAGMA table_info(swipe_events)").fetchall()}
    if "recent_rejection_rate" not in swipe_cols:
        conn.execute("ALTER TABLE swipe_events ADD COLUMN recent_rejection_rate REAL NOT NULL DEFAULT 0.0")
    if "days_since_last_session" not in swipe_cols:
        conn.execute("ALTER TABLE swipe_events ADD COLUMN days_since_last_session REAL NOT NULL DEFAULT 0.0")

    user_cols = {r["name"] for r in conn.execute("PRAGMA table_info(users)").fetchall()}
    if "email" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN email TEXT")
    if "password_hash" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
    if "password_changed_at" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN password_changed_at TIMESTAMP")
    if "token_issued_at" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN token_issued_at TIMESTAMP")
        conn.execute("UPDATE users SET token_issued_at = CURRENT_TIMESTAMP WHERE token_issued_at IS NULL")

    food_cols = {r["name"] for r in conn.execute("PRAGMA table_info(food_items)").fetchall()}
    if "embedding" not in food_cols:
        conn.execute("ALTER TABLE food_items ADD COLUMN embedding BLOB")
    if "image_slug" not in food_cols:
        conn.execute("ALTER TABLE food_items ADD COLUMN image_slug TEXT")
    if "image_hash" not in food_cols:
        conn.execute("ALTER TABLE food_items ADD COLUMN image_hash TEXT")
    if "image_author" not in food_cols:
        conn.execute("ALTER TABLE food_items ADD COLUMN image_author TEXT")
    if "image_license" not in food_cols:
        conn.execute("ALTER TABLE food_items ADD COLUMN image_license TEXT")
    if "image_source_url" not in food_cols:
        conn.execute("ALTER TABLE food_items ADD COLUMN image_source_url TEXT")
    if "image_review_status" not in food_cols:
        conn.execute("ALTER TABLE food_items ADD COLUMN image_review_status TEXT NOT NULL DEFAULT 'auto'")

    if "recent_likes_json" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN recent_likes_json TEXT")

    conn.execute(
        "CREATE TABLE IF NOT EXISTS user_item_impressions ("
        "  user_id INTEGER NOT NULL REFERENCES users(id),"
        "  food_item_id INTEGER NOT NULL REFERENCES food_items(id),"
        "  count INTEGER NOT NULL DEFAULT 0,"
        "  last_seen TIMESTAMP,"
        "  PRIMARY KEY (user_id, food_item_id)"
        ")"
    )

    try:
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE email IS NOT NULL"
        )
    except sqlite3.OperationalError:
        pass

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


def get_restaurant_by_name(conn: sqlite3.Connection, name: str) -> dict | None:
    row = conn.execute("SELECT * FROM restaurants WHERE name = ?", [name]).fetchone()
    return dict(row) if row else None


def get_food_item_by_name(conn: sqlite3.Connection, name: str, restaurant_id: int) -> dict | None:
    row = conn.execute(
        "SELECT * FROM food_items WHERE name = ? AND restaurant_id = ?", [name, restaurant_id]
    ).fetchone()
    return dict(row) if row else None


def get_recent_likes(conn: sqlite3.Connection, user_id: int) -> list[int]:
    row = conn.execute(
        "SELECT recent_likes_json FROM users WHERE id = ?", [user_id]
    ).fetchone()
    if row is None or not row["recent_likes_json"]:
        return []
    import json
    return json.loads(row["recent_likes_json"])


def push_recent_like(conn: sqlite3.Connection, user_id: int, item_id: int, max_len: int = 10) -> None:
    import json
    likes = get_recent_likes(conn, user_id)
    if item_id in likes:
        likes.remove(item_id)
    likes.append(item_id)
    if len(likes) > max_len:
        likes = likes[-max_len:]
    conn.execute(
        "UPDATE users SET recent_likes_json = ? WHERE id = ?",
        [json.dumps(likes), user_id],
    )
    conn.commit()


def get_embeddings_for_items(conn: sqlite3.Connection, item_ids: list[int]) -> list[bytes]:
    if not item_ids:
        return []
    placeholders = ",".join("?" * len(item_ids))
    rows = conn.execute(
        f"SELECT id, embedding FROM food_items WHERE id IN ({placeholders})",
        item_ids,
    ).fetchall()
    id_to_emb = {r["id"]: r["embedding"] for r in rows if r["embedding"]}
    return [id_to_emb[i] for i in item_ids if i in id_to_emb]


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

    diet_clauses, diet_args = build_dietary_filter_clauses(dietary_restrictions)
    clauses.extend(diet_clauses)
    args.extend(diet_args)

    if exclude_ids:
        placeholders = ",".join("?" * len(exclude_ids))
        clauses.append(f"id NOT IN ({placeholders})")
        args.extend(exclude_ids)

    query = (
        f"SELECT {_FOOD_ITEM_COLS_WITH_EMBEDDING} "
        "FROM food_items WHERE " + " AND ".join(clauses)
    )
    rows = conn.execute(query, args).fetchall()
    return [dict(r) for r in rows]


def get_food_item(conn: sqlite3.Connection, item_id: int) -> dict | None:
    row = conn.execute(
        f"SELECT {_FOOD_ITEM_COLS} FROM food_items WHERE id = ?",
        [item_id],
    ).fetchone()
    return dict(row) if row else None


def list_food_items(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        f"SELECT {_FOOD_ITEM_COLS} FROM food_items WHERE tagging_status = 'tagged'"
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


def get_user_by_email(conn: sqlite3.Connection, email: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?", [email.lower()]
    ).fetchone()
    return dict(row) if row else None


def attach_credentials(conn: sqlite3.Connection, user_id: int, email: str, password_hash: str) -> None:
    """Claim a guest row by attaching email + password (register-while-guest)."""
    conn.execute(
        "UPDATE users SET email = ?, password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        [email.lower(), password_hash, user_id],
    )
    conn.commit()


def create_registered_user(
    conn: sqlite3.Connection, email: str, password_hash: str, name: str
) -> tuple[int, str]:
    """Create a brand-new registered user (cold register). Returns (user_id, api_token)."""
    token = generate_api_token()
    cursor = conn.execute(
        "INSERT INTO users (name, api_token, email, password_hash) VALUES (?, ?, ?, ?)",
        [name, token, email.lower(), password_hash],
    )
    conn.commit()
    return cursor.lastrowid, token


def rotate_api_token(conn: sqlite3.Connection, user_id: int) -> str:
    new_token = generate_api_token()
    conn.execute(
        "UPDATE users SET api_token = ?, token_issued_at = CURRENT_TIMESTAMP, "
        "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        [new_token, user_id],
    )
    conn.commit()
    return new_token


def update_password(conn: sqlite3.Connection, user_id: int, password_hash: str) -> str:
    """Update password hash, record changed_at, rotate token. Returns new token."""
    new_token = generate_api_token()
    conn.execute(
        "UPDATE users SET password_hash = ?, password_changed_at = CURRENT_TIMESTAMP, "
        "api_token = ?, token_issued_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP "
        "WHERE id = ?",
        [password_hash, new_token, user_id],
    )
    conn.commit()
    return new_token


def hash_password(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode(), _bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode(), hashed.encode())


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


def record_impression(conn: sqlite3.Connection, user_id: int, item_id: int) -> None:
    conn.execute(
        "INSERT INTO user_item_impressions (user_id, food_item_id, count, last_seen) "
        "VALUES (?, ?, 1, CURRENT_TIMESTAMP) "
        "ON CONFLICT(user_id, food_item_id) DO UPDATE SET "
        "count = count + 1, last_seen = CURRENT_TIMESTAMP",
        [user_id, item_id],
    )
    conn.commit()


def get_least_impressed(conn: sqlite3.Connection, user_id: int, candidate_ids: list[int]) -> int:
    """Return the candidate_id with the fewest impressions for this user."""
    import json
    if not candidate_ids:
        raise ValueError("candidate_ids must be non-empty")
    row = conn.execute(
        "SELECT c.value AS id, COALESCE(i.count, 0) AS impression_count "
        "FROM json_each(?) c "
        "LEFT JOIN user_item_impressions i ON i.food_item_id = c.value AND i.user_id = ? "
        "ORDER BY impression_count ASC LIMIT 1",
        [json.dumps(candidate_ids), user_id],
    ).fetchone()
    return int(row["id"])


def get_items_without_embedding(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT id, name, description, cuisine_type, protein_type "
        "FROM food_items WHERE tagging_status = 'tagged' AND embedding IS NULL"
    ).fetchall()
    return [dict(r) for r in rows]


def update_food_item_image(
    conn: sqlite3.Connection,
    item_id: int,
    image_slug: str,
    image_hash: str,
    image_author: str,
    image_license: str,
    image_source_url: str,
    image_review_status: str = "auto",
) -> None:
    conn.execute(
        "UPDATE food_items SET image_slug = ?, image_hash = ?, image_author = ?, "
        "image_license = ?, image_source_url = ?, image_review_status = ?, "
        "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        [image_slug, image_hash, image_author, image_license, image_source_url,
         image_review_status, item_id],
    )
    conn.commit()


def get_items_without_image(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT id, name, cuisine_type FROM food_items "
        "WHERE tagging_status = 'tagged' AND image_slug IS NULL"
    ).fetchall()
    return [dict(r) for r in rows]


def update_food_item_embedding(conn: sqlite3.Connection, item_id: int, embedding: bytes) -> None:
    conn.execute(
        "UPDATE food_items SET embedding = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        [embedding, item_id],
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
