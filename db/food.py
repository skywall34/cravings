"""Food item, restaurant, embedding, image, and impression queries."""

import json
import sqlite3

from tagging.safety import build_dietary_filter_clauses

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


def get_food_item_by_name(
    conn: sqlite3.Connection, name: str, restaurant_id: int
) -> dict | None:
    row = conn.execute(
        "SELECT * FROM food_items WHERE name = ? AND restaurant_id = ?", [name, restaurant_id]
    ).fetchone()
    return dict(row) if row else None


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


def get_popular_food_items(
    conn: sqlite3.Connection,
    safety_mask: int,
    dietary_restrictions: list[str],
    exclude_ids: list[int] | None = None,
    limit: int = 10,
) -> list[dict]:
    """Rank food items by aggregate right-swipe rate across all users. Guest recommendations."""
    clauses = ["tagging_status = 'tagged'", "(safety_risk_bitmask & ?) = 0"]
    args: list = [safety_mask]

    diet_clauses, diet_args = build_dietary_filter_clauses(dietary_restrictions)
    clauses.extend(diet_clauses)
    args.extend(diet_args)

    if exclude_ids:
        placeholders = ",".join("?" * len(exclude_ids))
        clauses.append(f"f.id NOT IN ({placeholders})")
        args.extend(exclude_ids)

    args.append(limit)
    where = " AND ".join(clauses)
    query = (
        f"SELECT f.{_FOOD_ITEM_COLS.replace(', ', ', f.')}, "
        "COALESCE("
        "  SUM(CASE WHEN s.direction = 'right' THEN 1.0 ELSE 0.0 END)"
        "  / NULLIF(COUNT(s.id), 0), 0.0"
        ") AS popularity_score "
        "FROM food_items f "
        "LEFT JOIN swipe_events s ON s.food_item_id = f.id "
        f"WHERE {where} "
        "GROUP BY f.id "
        "ORDER BY popularity_score DESC, RANDOM() "
        "LIMIT ?"
    )
    rows = conn.execute(query, args).fetchall()
    return [dict(r) for r in rows]


def list_restaurants(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT id, name, COALESCE(location, '') as location, "
        "COALESCE(cuisine_type, '') as cuisine_type, source_type FROM restaurants"
    ).fetchall()
    return [dict(r) for r in rows]


def record_impression(conn: sqlite3.Connection, user_id: int, item_id: int) -> None:
    conn.execute(
        "INSERT INTO user_item_impressions (user_id, food_item_id, count, last_seen) "
        "VALUES (?, ?, 1, CURRENT_TIMESTAMP) "
        "ON CONFLICT(user_id, food_item_id) DO UPDATE SET "
        "count = count + 1, last_seen = CURRENT_TIMESTAMP",
        [user_id, item_id],
    )
    conn.commit()


def get_least_impressed(
    conn: sqlite3.Connection, user_id: int, candidate_ids: list[int]
) -> int:
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


def get_items_without_image(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT id, name, cuisine_type FROM food_items "
        "WHERE tagging_status = 'tagged' AND image_slug IS NULL"
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


def update_food_item_embedding(
    conn: sqlite3.Connection, item_id: int, embedding: bytes
) -> None:
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

    # Tagger cuisine is unreliable for dishes with culturally ambiguous names.
    # Prefer the restaurant's cuisine_type when it is set to a specific cuisine.
    row = conn.execute(
        "SELECT r.cuisine_type FROM food_items fi "
        "JOIN restaurants r ON r.id = fi.restaurant_id "
        "WHERE fi.id = ?",
        [item_id],
    ).fetchone()
    if row and row[0] and row[0] != "other":
        present["cuisine_type"] = row[0]

    set_clause = ", ".join(f"{k} = ?" for k in present.keys())
    conn.execute(
        f"UPDATE food_items SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        [*present.values(), item_id],
    )
    conn.commit()
