"""Openverse API image search for food items."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import httpx

from tagging.wikimedia import ALLOWED_LICENSES, _HEADERS, _is_allowed_license

OPENVERSE_API = "https://api.openverse.org/v1/images/"

_LICENSE_MAP = {
    ("by", "4.0"): "CC-BY-4.0",
    ("by", "3.0"): "CC-BY-3.0",
    ("by", "2.0"): "CC-BY-2.0",
    ("by-sa", "4.0"): "CC-BY-SA-4.0",
    ("by-sa", "3.0"): "CC-BY-SA-3.0",
    ("by-sa", "2.0"): "CC-BY-SA-2.0",
    ("cc0", ""): "CC0",
    ("cc0", "1.0"): "CC0",
    ("pdm", ""): "PD",
    ("pdm", "1.0"): "PD",
}


@dataclass
class OpenverseResult:
    url: str                  # direct image URL
    foreign_landing_url: str  # attribution page
    license: str              # canonical license string (e.g. CC-BY-SA-4.0)
    creator: str


def _map_license(license_code: str, license_version: str) -> Optional[str]:
    code = license_code.lower().strip()
    ver = (license_version or "").strip()
    mapped = _LICENSE_MAP.get((code, ver)) or _LICENSE_MAP.get((code, ""))
    if mapped and _is_allowed_license(mapped):
        return mapped
    return None


def search_openverse(
    query: str,
    client: httpx.Client,
    limit: int = 5,
) -> list[OpenverseResult]:
    """Search Openverse for CC-licensed food images. Returns up to limit results."""
    params = {
        "q": query,
        "license": "by,by-sa,cc0,pdm",
        "page_size": min(limit * 2, 20),  # over-fetch, filter below
        "format": "json",
    }
    try:
        resp = client.get(
            OPENVERSE_API,
            params=params,
            headers=_HEADERS,
            timeout=15,
        )
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", "10"))
            time.sleep(retry_after)
            resp = client.get(OPENVERSE_API, params=params, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
    except httpx.RequestError:
        return []

    results: list[OpenverseResult] = []
    for item in resp.json().get("results", []):
        license_code = item.get("license", "")
        license_version = item.get("license_version", "")
        mapped = _map_license(license_code, license_version)
        if mapped is None:
            continue
        url = item.get("url", "")
        if not url:
            continue
        results.append(OpenverseResult(
            url=url,
            foreign_landing_url=item.get("foreign_landing_url", url),
            license=mapped,
            creator=item.get("creator", "") or "Unknown",
        ))
        if len(results) >= limit:
            break

    return results
