"""Fetch and process food item images from Wikimedia.

Usage:
    uv run python scripts/fetch_food_images.py [--limit N] [--dry-run] [--force]
    uv run python scripts/fetch_food_images.py --manual
    uv run python scripts/fetch_food_images.py --placeholders
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import sys
import time
from io import BytesIO
from pathlib import Path

import httpx
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent))

import db.database as db
from tagging.wikimedia import (
    Attribution,
    find_image,
    fetch_metadata,
    download_and_hash,
)

IMAGES_ROOT = Path(os.environ.get("CRAVINGS_IMAGES_ROOT", "./images"))
DB_PATH = Path(os.environ.get("CRAVINGS_DB", "cravings.db"))
MISSING_CSV = IMAGES_ROOT / "missing.csv"

TARGET_SIZES = [400, 800]
WEBP_QUALITY = 80

CUISINE_LIST = [
    "american", "chinese", "indian", "italian", "japanese",
    "korean", "mediterranean", "mexican", "middle_eastern", "other", "thai",
]

CUISINE_SEARCH_TERMS = {
    "american": "American cuisine",
    "chinese": "Chinese cuisine",
    "indian": "Indian cuisine",
    "italian": "Italian cuisine",
    "japanese": "Japanese cuisine",
    "korean": "Korean cuisine",
    "mediterranean": "Mediterranean cuisine",
    "mexican": "Mexican cuisine",
    "middle_eastern": "Middle Eastern cuisine",
    "other": "world cuisine food",
    "thai": "Thai cuisine",
}


def _slugify(name: str) -> str:
    import re
    s = name.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")[:40]


def _center_crop_4_3(img: Image.Image) -> Image.Image:
    """Center-crop image to 4:3 aspect ratio."""
    w, h = img.size
    target_ratio = 4 / 3
    current_ratio = w / h
    if current_ratio > target_ratio:
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    elif current_ratio < target_ratio:
        new_h = int(w / target_ratio)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))
    return img


def _process_and_save(raw_bytes: bytes, slug: str, hash_: str, food_dir: Path) -> None:
    """Center-crop, resize to 400/800, save as webp."""
    img = Image.open(BytesIO(raw_bytes)).convert("RGB")
    img = _center_crop_4_3(img)
    for width in TARGET_SIZES:
        height = int(width * 3 / 4)
        resized = img.resize((width, height), Image.LANCZOS)
        out = food_dir / f"{slug}-{hash_}-{width}.webp"
        resized.save(out, "WEBP", quality=WEBP_QUALITY)


def _append_missing(item_id: int, name: str, cuisine: str, reason: str, url: str) -> None:
    MISSING_CSV.parent.mkdir(parents=True, exist_ok=True)
    write_header = not MISSING_CSV.exists()
    with open(MISSING_CSV, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["id", "name", "cuisine_type", "reason", "wikimedia_url_attempted"])
        writer.writerow([item_id, name, cuisine, reason, url])


def process_one(
    item: dict,
    client: httpx.Client,
    food_dir: Path,
    dry_run: bool,
    force: bool,
) -> bool:
    """Fetch, process and DB-update one item. Returns True on success."""
    item_id = item["id"]
    name = item["name"]
    cuisine = item.get("cuisine_type") or ""
    slug = _slugify(name)

    print(f"  [{item_id}] {name} ({cuisine}) ...", end=" ", flush=True)

    candidate = find_image(name, cuisine, client)
    time.sleep(1)

    if candidate is None:
        print("no image found")
        _append_missing(item_id, name, cuisine, "no_candidate", "")
        return False

    attribution = fetch_metadata(candidate.file_page, client)
    time.sleep(1)

    if attribution is None:
        print("license rejected")
        _append_missing(item_id, name, cuisine, "license_rejected", candidate.file_page)
        return False

    if dry_run:
        review = "needs_review" if candidate.review_needed else "auto"
        print(f"DRY RUN tier={candidate.tier} -> {slug}-????-400.webp [{review}]")
        return True

    try:
        raw_bytes, hash_ = download_and_hash(candidate.file_page, client)
    except Exception as e:
        print(f"download failed: {e}")
        _append_missing(item_id, name, cuisine, f"download_error:{e}", candidate.file_page)
        return False

    food_dir.mkdir(parents=True, exist_ok=True)
    try:
        _process_and_save(raw_bytes, slug, hash_, food_dir)
    except Exception as e:
        print(f"image processing failed: {e}")
        _append_missing(item_id, name, cuisine, f"processing_error:{e}", candidate.file_page)
        return False

    review_status = "needs_review" if candidate.review_needed else "auto"

    with db.db_connection(DB_PATH) as conn:
        db.update_food_item_image(
            conn, item_id, slug, hash_,
            attribution.author, attribution.license, attribution.source_url,
            review_status,
        )

    if candidate.review_needed:
        _append_missing(item_id, name, cuisine, f"tier3_needs_review", candidate.file_page)

    print(f"tier={candidate.tier} -> {slug}-{hash_}-400.webp [{review_status}]")
    return True


def cmd_fetch(args: argparse.Namespace) -> None:
    food_dir = IMAGES_ROOT / "food"

    with db.db_connection(DB_PATH) as conn:
        if args.force:
            items = conn.execute(
                "SELECT id, name, cuisine_type FROM food_items WHERE tagging_status='tagged'"
            ).fetchall()
            items = [dict(r) for r in items]
        else:
            items = db.get_items_without_image(conn)

    if args.limit:
        items = items[: args.limit]

    print(f"Processing {len(items)} items (dry_run={args.dry_run}, force={args.force})")

    success = 0
    with httpx.Client() as client:
        for item in items:
            ok = process_one(item, client, food_dir, args.dry_run, args.force)
            if ok:
                success += 1

    print(f"\nDone: {success}/{len(items)} succeeded")


def cmd_manual(args: argparse.Namespace) -> None:
    """Process manually placed images from images/manual/."""
    manual_dir = IMAGES_ROOT / "manual"
    processed_dir = manual_dir / "_processed"
    food_dir = IMAGES_ROOT / "food"

    if not manual_dir.exists():
        print(f"Manual dir not found: {manual_dir}")
        return

    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
    ALLOWED_LICENSES = {
        "CC0", "CC-BY", "CC-BY-2.0", "CC-BY-3.0", "CC-BY-4.0",
        "CC-BY-SA", "CC-BY-SA-2.0", "CC-BY-SA-3.0", "CC-BY-SA-4.0",
        "PD", "Public domain",
    }

    image_files = [
        f for f in manual_dir.iterdir()
        if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS
    ]

    if not image_files:
        print("No image files found in images/manual/")
        return

    success = 0
    for img_path in image_files:
        slug = img_path.stem
        sidecar = manual_dir / f"{slug}.attribution.json"

        if not sidecar.exists():
            print(f"  SKIP {img_path.name}: missing sidecar {sidecar.name}")
            continue

        try:
            attr = json.loads(sidecar.read_text())
        except Exception as e:
            print(f"  SKIP {img_path.name}: bad sidecar JSON: {e}")
            continue

        item_id = attr.get("item_id")
        author = attr.get("author", "").strip()
        license_ = attr.get("license", "").strip()
        source_url = attr.get("source_url", "").strip()

        if not item_id or not author or not license_ or not source_url:
            print(f"  SKIP {img_path.name}: sidecar missing required fields (item_id, author, license, source_url)")
            continue

        if license_ not in ALLOWED_LICENSES:
            print(f"  SKIP {img_path.name}: license '{license_}' not in allow-list")
            continue

        with db.db_connection(DB_PATH) as conn:
            row = conn.execute("SELECT id FROM food_items WHERE id = ?", [item_id]).fetchone()
            if row is None:
                print(f"  SKIP {img_path.name}: item_id {item_id} not found in DB")
                continue

        raw_bytes = img_path.read_bytes()
        import hashlib
        hash_ = hashlib.sha256(raw_bytes).hexdigest()[:8]

        food_dir.mkdir(parents=True, exist_ok=True)
        _process_and_save(raw_bytes, slug, hash_, food_dir)

        with db.db_connection(DB_PATH) as conn:
            db.update_food_item_image(
                conn, item_id, slug, hash_, author, license_, source_url, "approved"
            )

        processed_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(img_path), str(processed_dir / img_path.name))
        shutil.move(str(sidecar), str(processed_dir / sidecar.name))

        print(f"  OK {img_path.name} -> {slug}-{hash_}-400.webp [approved]")
        success += 1

    print(f"\nManual: {success}/{len(image_files)} processed")


def cmd_placeholders(args: argparse.Namespace) -> None:
    """Auto-fetch one representative image per cuisine for placeholder use."""
    cuisines_dir = IMAGES_ROOT / "cuisines"
    cuisines_dir.mkdir(parents=True, exist_ok=True)

    attribution_file = cuisines_dir / "ATTRIBUTION.md"
    new_entries: list[str] = []

    with httpx.Client() as client:
        for cuisine in CUISINE_LIST:
            out_400 = cuisines_dir / f"{cuisine}.webp"
            if out_400.exists() and not args.force:
                print(f"  SKIP {cuisine} (already exists)")
                continue

            search_term = CUISINE_SEARCH_TERMS.get(cuisine, cuisine)
            print(f"  {cuisine}: searching for '{search_term}' ...", end=" ", flush=True)

            from tagging.wikimedia import find_image_tier3, find_image_tier2, find_image_tier1
            candidate = find_image_tier2(search_term, "", client)
            if candidate is None:
                time.sleep(0.5)
                candidate = find_image_tier3(search_term, client)

            time.sleep(1)

            if candidate is None:
                print("no image found — skipping")
                continue

            attribution = fetch_metadata(candidate.file_page, client)
            time.sleep(1)

            if attribution is None:
                print("license rejected — skipping")
                continue

            try:
                raw_bytes, _ = download_and_hash(candidate.file_page, client)
            except Exception as e:
                print(f"download failed: {e}")
                continue

            img = Image.open(BytesIO(raw_bytes)).convert("RGB")
            img = _center_crop_4_3(img)
            # Placeholders: only 400w
            width, height = 400, 300
            img = img.resize((width, height), Image.LANCZOS)
            img.save(out_400, "WEBP", quality=WEBP_QUALITY)

            new_entries.append(
                f"## {cuisine.replace('_', ' ').title()}\n"
                f"- Author: {attribution.author}\n"
                f"- License: {attribution.license}\n"
                f"- Source: {attribution.source_url}\n"
            )

            print(f"saved {out_400.name} ({attribution.license})")

    if new_entries:
        existing = attribution_file.read_text() if attribution_file.exists() else "# Cuisine Placeholder Attribution\n"
        attribution_file.write_text(existing.rstrip() + "\n\n" + "\n\n".join(new_entries) + "\n")
        print(f"\nPlaceholders done. {len(new_entries)} entries appended to {attribution_file}")
    else:
        print("\nPlaceholders done. No new entries.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch food images from Wikimedia")
    sub = parser.add_subparsers(dest="cmd")

    fetch_p = sub.add_parser("fetch", help="Fetch from Wikimedia (default)")
    fetch_p.add_argument("--limit", type=int, default=0, help="Max items to process (0=all)")
    fetch_p.add_argument("--dry-run", action="store_true")
    fetch_p.add_argument("--force", action="store_true", help="Re-fetch items that already have images")

    sub.add_parser("manual", help="Process manually placed images")

    placeholder_p = sub.add_parser("placeholders", help="Fetch cuisine placeholder images")
    placeholder_p.add_argument("--force", action="store_true")

    # Support flat flags as shorthand for 'fetch' subcommand
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--manual", action="store_true")
    parser.add_argument("--placeholders", action="store_true")

    args = parser.parse_args()

    if args.manual or args.cmd == "manual":
        cmd_manual(args)
    elif args.placeholders or args.cmd == "placeholders":
        cmd_placeholders(args)
    else:
        cmd_fetch(args)


if __name__ == "__main__":
    main()
