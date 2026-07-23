"""Ingest AI-generated PNGs from images/missing/ for items with no image_slug.

Filenames are matched against food_items.name via _slugify() (hyphenated,
accent-preserving) and its ascii-folded form. Two filenames are typos of the
real item names and are hardcoded overrides.

Usage:
    uv run python scripts/ingest_missing_images.py --dry-run
    uv run python scripts/ingest_missing_images.py
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import db.database as db
from db.food import get_items_without_image
from scripts.fetch_food_images import _slugify, _process_and_save

DB_PATH = Path(os.environ.get("CRAVINGS_DB", "cravings.db"))
MISSING_DIR = Path(__file__).parent.parent / "images" / "missing"
PROCESSED_DIR = MISSING_DIR / "_processed"
FOOD_DIR = Path(__file__).parent.parent / "images" / "food"

# filename stem (no extension) -> item_id, for names the normal slug match misses
TYPO_OVERRIDES = {
    "bit_beans_combo": 199,       # Pit Beans Combo
    "kataklete_kilkil": 872,      # Yataklete Kilkil
}


def _ascii_fold(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")


def _normalize_filename_stem(stem: str) -> str:
    s = stem.lower().replace("_", "-")
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def build_file_to_item_map(items: list[dict], png_files: list[Path]) -> tuple[dict[Path, dict], list[Path]]:
    """Return (file -> item dict, unmatched files)."""
    slug_to_item = {}
    ascii_slug_to_item = {}
    for item in items:
        slug = _slugify(item["name"])
        slug_to_item[slug] = item
        ascii_slug_to_item[_ascii_fold(slug)] = item

    id_to_item = {item["id"]: item for item in items}

    file_to_item: dict[Path, dict] = {}
    unmatched: list[Path] = []
    for png in png_files:
        norm = _normalize_filename_stem(png.stem)
        if png.stem in TYPO_OVERRIDES:
            item_id = TYPO_OVERRIDES[png.stem]
            if item_id in id_to_item:
                file_to_item[png] = id_to_item[item_id]
                continue
        if norm in slug_to_item:
            file_to_item[png] = slug_to_item[norm]
        elif norm in ascii_slug_to_item:
            file_to_item[png] = ascii_slug_to_item[norm]
        else:
            unmatched.append(png)

    return file_to_item, unmatched


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with db.db_connection(DB_PATH) as conn:
        items = get_items_without_image(conn)

    png_files = sorted(MISSING_DIR.glob("*.png"))
    file_to_item, unmatched = build_file_to_item_map(items, png_files)

    matched_item_ids = {item["id"] for item in file_to_item.values()}
    missing_item_ids = {item["id"] for item in items} - matched_item_ids

    print(f"{len(items)} items missing image_slug; {len(png_files)} PNGs found; "
          f"{len(file_to_item)} matched; {len(unmatched)} unmatched (orphans, skipped).")

    if unmatched:
        print("Unmatched (orphan) files:")
        for f in unmatched:
            print(f"  {f.name}")

    if missing_item_ids:
        print("ERROR: items with no matching PNG file:")
        for item in items:
            if item["id"] in missing_item_ids:
                print(f"  [{item['id']}] {item['name']}")
        sys.exit(1)

    assert len(file_to_item) == len(items), "matched count must equal missing-item count"

    if args.dry_run:
        print("\nDRY RUN mapping:")
        for png, item in sorted(file_to_item.items(), key=lambda kv: kv[1]["id"]):
            slug = _slugify(item["name"])
            print(f"  [{item['id']}] {item['name']} <- {png.name}  -> slug={slug}")
        print(f"\nDry run: would write {len(file_to_item)} items x2 webp files, "
              f"touch nothing.")
        return

    FOOD_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    done = 0
    with db.db_connection(DB_PATH) as conn:
        for png, item in sorted(file_to_item.items(), key=lambda kv: kv[1]["id"]):
            item_id = item["id"]
            name = item["name"]
            slug = _slugify(name)
            raw_bytes = png.read_bytes()
            hash_ = hashlib.sha256(raw_bytes).hexdigest()[:8]

            _process_and_save(raw_bytes, slug, hash_, FOOD_DIR)
            db.update_food_item_image(
                conn, item_id, slug, hash_,
                "AI generated", "proprietary", "",
                "approved",
            )
            shutil.move(str(png), str(PROCESSED_DIR / png.name))
            print(f"  [{item_id}] {name} -> {slug}-{hash_}-{{400,800}}.webp")
            done += 1

    print(f"\nDone. {done} items ingested.")


if __name__ == "__main__":
    main()
