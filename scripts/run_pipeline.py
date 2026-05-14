"""Run the full tagging pipeline: seed DB → tag via Ollama → store results."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import (
    init_db, insert_restaurant, insert_food_item,
    get_untagged_items, update_food_item_tags,
    get_restaurant_by_name, get_food_item_by_name,
)
from tagging.client import tag_food_item
from scripts.seed_data import SEED_RESTAURANTS, SEED_FOOD_ITEMS


def seed_database(db_path: Path | None = None):
    conn = init_db(db_path) if db_path else init_db()
    print(f"Database initialized at {db_path or 'default path'}")

    restaurant_ids = []
    for r in SEED_RESTAURANTS:
        existing = get_restaurant_by_name(conn, r['name'])
        if existing:
            rid = existing['id']
            print(f"  Restaurant (exists): {r['name']} (id={rid})")
        else:
            rid = insert_restaurant(conn, r)
            print(f"  Restaurant: {r['name']} (id={rid})")
        restaurant_ids.append(rid)

    for rest_idx, name, desc in SEED_FOOD_ITEMS:
        rid = restaurant_ids[rest_idx]
        existing = get_food_item_by_name(conn, name, rid)
        if existing:
            print(f"  Food item (exists): {name}")
        else:
            fid = insert_food_item(conn, {
                "name": name,
                "description": desc,
                "restaurant_id": rid,
            })
            print(f"  Food item: {name} (id={fid})")

    print(f"\nSeeded {len(SEED_RESTAURANTS)} restaurants, {len(SEED_FOOD_ITEMS)} food items")
    return conn


def tag_all_untagged(conn):
    items = get_untagged_items(conn)
    print(f"\n{len(items)} items to tag")

    tagged = 0
    failed = 0
    for item in items:
        name = item["name"]
        desc = item.get("description")
        try:
            print(f"  Tagging: {name}...", end=" ", flush=True)
            tags = tag_food_item(name, desc)
            update_food_item_tags(conn, item["id"], tags)
            print("OK")
            tagged += 1
        except Exception as e:
            print(f"FAILED: {e}")
            conn.execute(
                "UPDATE food_items SET tagging_status = 'failed' WHERE id = ?",
                [item["id"]],
            )
            conn.commit()
            failed += 1
        time.sleep(0.5)  # rate limit

    print(f"\nTagging complete: {tagged} tagged, {failed} failed")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Cravings tagging pipeline")
    parser.add_argument("--db", type=str, help="Database path (default: cravings.db)")
    parser.add_argument("--seed-only", action="store_true", help="Only seed, don't tag")
    parser.add_argument("--tag-only", action="store_true", help="Only tag existing untagged items")
    args = parser.parse_args()

    db_path = Path(args.db) if args.db else None

    if args.tag_only:
        from db.database import get_connection
        conn = get_connection(db_path) if db_path else get_connection()
        tag_all_untagged(conn)
    else:
        conn = seed_database(db_path)
        if not args.seed_only:
            tag_all_untagged(conn)

    conn.close()


if __name__ == "__main__":
    main()
