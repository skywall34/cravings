"""Wikimedia/Wikidata image lookup for food items."""

from __future__ import annotations

import hashlib
import re
import time
import urllib.parse
from dataclasses import dataclass
from typing import Optional

import httpx

ALLOWED_LICENSES = frozenset({
    "CC0", "CC-BY", "CC-BY-2.0", "CC-BY-3.0", "CC-BY-4.0",
    "CC-BY-SA", "CC-BY-SA-2.0", "CC-BY-SA-3.0", "CC-BY-SA-4.0",
    "Public domain", "PD", "PD-old", "PD-self",
})

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"

_HEADERS = {"User-Agent": "cravings-image-fetcher/1.0 (https://github.com/skywall34/cravings; doshinkorean@gmail.com)"}


@dataclass
class ImageCandidate:
    file_page: str       # Wikimedia Commons file page URL
    tier: int            # 1, 2, or 3
    review_needed: bool  # True for tier-3


@dataclass
class Attribution:
    author: str
    license: str
    source_url: str


def _normalize_license(raw: str) -> str:
    """Normalize Wikimedia license string to a short canonical form."""
    raw = raw.strip()
    # Strip HTML tags
    raw = re.sub(r"<[^>]+>", "", raw)
    # Strip locale port suffixes after version numbers (e.g. "CC BY-SA 2.0 kr" → "CC BY-SA 2.0",
    # "cc-by-sa-2.0-kr" → "cc-by-sa-2.0"). Lookbehind on digit prevents stripping "Public Domain".
    raw = re.sub(r"(?<=\d)[-\s][a-z]{2,3}$", "", raw, flags=re.IGNORECASE).strip()
    # Map common verbose forms
    mapping = {
        "Creative Commons Attribution-Share Alike 4.0": "CC-BY-SA-4.0",
        "Creative Commons Attribution-Share Alike 3.0": "CC-BY-SA-3.0",
        "Creative Commons Attribution-Share Alike 2.0": "CC-BY-SA-2.0",
        "Creative Commons Attribution 4.0": "CC-BY-4.0",
        "Creative Commons Attribution 3.0": "CC-BY-3.0",
        "Creative Commons Attribution 2.0": "CC-BY-2.0",
        "CC BY-SA 4.0": "CC-BY-SA-4.0",
        "CC BY-SA 3.0": "CC-BY-SA-3.0",
        "CC BY-SA 2.0": "CC-BY-SA-2.0",
        "CC BY 4.0": "CC-BY-4.0",
        "CC BY 3.0": "CC-BY-3.0",
        "CC BY 2.0": "CC-BY-2.0",
        "Public Domain": "PD",
        "public domain": "PD",
    }
    return mapping.get(raw, raw)


def _is_allowed_license(license_str: str) -> bool:
    if not license_str or not license_str.strip():
        return False
    normalized = _normalize_license(license_str)
    if normalized in ALLOWED_LICENSES:
        return True
    for allowed in ALLOWED_LICENSES:
        if allowed.lower() in normalized.lower() or normalized.lower() in allowed.lower():
            return True
    return False


def fetch_metadata(file_page: str, client: httpx.Client) -> Optional[Attribution]:
    """Fetch image metadata from Wikimedia Commons. Returns None if license rejected."""
    # Extract filename from URL like https://commons.wikimedia.org/wiki/File:Foo.jpg
    match = re.search(r"(?:File:|Special:FilePath/)(.+?)(?:\?|$)", file_page)
    if not match:
        return None
    filename = urllib.parse.unquote(match.group(1)).replace(" ", "_")

    resp = client.get(
        "https://commons.wikimedia.org/w/api.php",
        params={
            "action": "query",
            "titles": f"File:{filename}",
            "prop": "imageinfo",
            "iiprop": "extmetadata|url",
            "format": "json",
        },
        headers=_HEADERS,
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    pages = data.get("query", {}).get("pages", {})
    page = next(iter(pages.values()), {})
    imageinfo = (page.get("imageinfo") or [{}])[0]
    extmeta = imageinfo.get("extmetadata", {})

    license_raw = extmeta.get("LicenseShortName", {}).get("value", "")
    if not license_raw:
        license_raw = extmeta.get("License", {}).get("value", "")

    if not _is_allowed_license(license_raw):
        return None

    artist_raw = extmeta.get("Artist", {}).get("value", "")
    artist = re.sub(r"<[^>]+>", "", artist_raw).strip() or "Unknown"

    source_url = imageinfo.get("descriptionurl") or file_page

    return Attribution(
        author=artist,
        license=_normalize_license(license_raw),
        source_url=source_url,
    )


def _commons_file_url(image_value: str) -> str:
    """Convert a Wikidata P18 image value to a Wikimedia Commons file page URL."""
    name = image_value.rsplit("/", 1)[-1]
    name = name.replace(" ", "_")
    return f"https://commons.wikimedia.org/wiki/File:{name}"


def find_image_tier1(item_name: str, client: httpx.Client) -> Optional[ImageCandidate]:
    """Wikidata SPARQL: exact English label + has P18 image (any entity type)."""
    query = f"""
SELECT ?image WHERE {{
  ?item rdfs:label "{item_name}"@en ;
        wdt:P18 ?image .
}}
LIMIT 1
"""
    try:
        resp = client.get(
            SPARQL_ENDPOINT,
            params={"query": query, "format": "json"},
            headers={**_HEADERS, "Accept": "application/sparql-results+json"},
            timeout=20,
        )
        if resp.status_code == 429:
            return None  # Rate limited — fall through to tier 2
        resp.raise_for_status()
        bindings = resp.json().get("results", {}).get("bindings", [])
        if bindings:
            image_url = bindings[0]["image"]["value"]
            file_page = _commons_file_url(image_url)
            return ImageCandidate(file_page=file_page, tier=1, review_needed=False)
    except Exception:
        pass
    return None


def _image_from_wikipedia_summary(title: str, tier: int, client: httpx.Client) -> Optional[ImageCandidate]:
    """Use Wikipedia REST summary API to get originalimage for a title.
    Tries the exact title first, then a lowercase-words variant.
    """
    candidates = [title]
    # Wikipedia convention: first letter caps, rest lowercase words
    words = title.split()
    if len(words) > 1:
        lower_variant = words[0] + " " + " ".join(w.lower() for w in words[1:])
        if lower_variant != title:
            candidates.append(lower_variant)

    for candidate in candidates:
        slug = candidate.replace(" ", "_")
        try:
            resp = client.get(
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}",
                headers=_HEADERS,
                timeout=15,
                follow_redirects=True,
            )
            if resp.status_code == 404:
                continue
            resp.raise_for_status()
            data = resp.json()
            if data.get("type") == "disambiguation":
                continue
            orig = data.get("originalimage") or data.get("thumbnail")
            if not orig:
                continue
            source = orig.get("source", "")
            if not source:
                continue
            # Thumbnail URLs: .../thumb/x/xx/Original_file.jpg/800px-Original_file.jpg
            # Extract the actual filename (third component after /thumb/).
            # URL-decode to convert %2C etc. back to characters for Commons API lookup.
            if "/thumb/" in source:
                parts = source.split("/thumb/")[-1].split("/")
                filename = parts[2] if len(parts) >= 3 else parts[-1]
            else:
                filename = source.rsplit("/", 1)[-1].split("?")[0]
            filename = urllib.parse.unquote(filename)
            file_page = f"https://commons.wikimedia.org/wiki/File:{filename}"
            return ImageCandidate(file_page=file_page, tier=tier, review_needed=(tier == 3))
        except Exception:
            pass
    return None


def find_image_tier2(item_name: str, cuisine_type: str, client: httpx.Client) -> Optional[ImageCandidate]:
    """Wikipedia REST summary on disambiguated title '{name} ({cuisine} dish)'."""
    disambig_title = f"{item_name} ({cuisine_type} dish)"
    result = _image_from_wikipedia_summary(disambig_title, 2, client)
    if result:
        return result
    # Also try '{name} (dish)' without cuisine qualifier
    return _image_from_wikipedia_summary(f"{item_name} (dish)", 2, client)


def find_image_tier3(item_name: str, client: httpx.Client) -> Optional[ImageCandidate]:
    """Wikipedia REST summary on plain title (may be wrong — needs_review)."""
    return _image_from_wikipedia_summary(item_name, 3, client)


def find_image(item_name: str, cuisine_type: str, client: httpx.Client) -> Optional[ImageCandidate]:
    """Run tier 1 → 2 → 3 disambiguation. Returns first hit or None."""
    candidate = find_image_tier1(item_name, client)
    if candidate:
        return candidate

    time.sleep(0.5)
    candidate = find_image_tier2(item_name, cuisine_type, client)
    if candidate:
        return candidate

    time.sleep(0.5)
    candidate = find_image_tier3(item_name, client)
    return candidate


def download_and_hash(image_url_or_file_page: str, client: httpx.Client) -> tuple[bytes, str]:
    """Download image bytes from a Wikimedia Commons file page or direct URL.
    Returns (bytes, sha256[:8] hash).
    """
    # If it's a file page, get the actual image URL first
    if "wiki/File:" in image_url_or_file_page or "Special:FilePath" in image_url_or_file_page:
        filename = re.search(r"File:(.+?)(?:\?|$)", image_url_or_file_page)
        if filename:
            fname = urllib.parse.unquote(filename.group(1)).replace(" ", "_")
            resp = client.get(
                "https://commons.wikimedia.org/w/api.php",
                params={
                    "action": "query",
                    "titles": f"File:{fname}",
                    "prop": "imageinfo",
                    "iiprop": "url",
                    "format": "json",
                },
                headers=_HEADERS,
                timeout=15,
            )
            resp.raise_for_status()
            pages = resp.json().get("query", {}).get("pages", {})
            page = next(iter(pages.values()), {})
            imageinfo = (page.get("imageinfo") or [{}])[0]
            direct_url = imageinfo.get("url", "")
            if direct_url:
                img_resp = client.get(direct_url, headers=_HEADERS, timeout=30, follow_redirects=True)
                img_resp.raise_for_status()
                data = img_resp.content
                hash_ = hashlib.sha256(data).hexdigest()[:8]
                return data, hash_

    # Direct URL
    resp = client.get(image_url_or_file_page, headers=_HEADERS, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    data = resp.content
    hash_ = hashlib.sha256(data).hexdigest()[:8]
    return data, hash_
