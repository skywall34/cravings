"""Compute and store embeddings for all tagged food items missing one."""

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import get_connection, get_items_without_embedding, update_food_item_embedding
from tagging.client import get_embedding


def build_embed_text(item: dict) -> str:
    parts = [item["name"]]
    if item.get("description"):
        parts.append(item["description"])
    if item.get("cuisine_type"):
        parts.append(f"cuisine: {item['cuisine_type']}")
    if item.get("protein_type"):
        parts.append(f"protein: {item['protein_type']}")
    return ". ".join(parts)


def embed_all(conn, validate: bool = False):
    items = get_items_without_embedding(conn)
    print(f"{len(items)} items need embeddings")

    done = 0
    failed = 0
    for item in items:
        text = build_embed_text(item)
        try:
            print(f"  Embedding: {item['name']}...", end=" ", flush=True)
            vec = get_embedding(text)
            update_food_item_embedding(conn, item["id"], vec.tobytes())
            print("OK")
            done += 1
        except Exception as e:
            print(f"FAILED: {e}")
            failed += 1
        time.sleep(0.1)

    print(f"\nDone: {done} embedded, {failed} failed")

    if validate:
        run_validation(conn)


def run_validation(conn):
    from db.database import get_connection as _gc
    rows = conn.execute(
        "SELECT id, name, embedding FROM food_items WHERE embedding IS NOT NULL"
    ).fetchall()
    if not rows:
        print("No embeddings to validate")
        return

    items = [(r["id"], r["name"], np.frombuffer(r["embedding"], dtype=np.float32)) for r in rows]

    target_name = "Tonkotsu Ramen"
    target = next((v for _, n, v in items if n == target_name), None)
    if target is None:
        # Fall back to first item
        _, target_name, target = items[0]

    sims = [(name, float(vec @ target)) for _, name, vec in items if name != target_name]
    sims.sort(key=lambda x: x[1], reverse=True)

    print(f"\nTop-5 neighbors of '{target_name}':")
    for name, score in sims[:5]:
        print(f"  {score:.3f}  {name}")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=str)
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()

    db_path = Path(args.db) if args.db else None
    conn = get_connection(db_path) if db_path else get_connection()
    embed_all(conn, validate=args.validate)
    conn.close()


if __name__ == "__main__":
    main()
