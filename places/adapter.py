"""Adapter for Google Places (Text Search v1) with stub fallback when no API key."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

PLACES_URL = "https://places.googleapis.com/v1/places:searchText"

_STUB_PLACES: list[dict] = [
    {"name": "Demo Kitchen", "address": "123 Main St", "rating": 4.5, "maps_url": "https://maps.google.com"},
    {"name": "Test Bistro", "address": "456 Elm Ave", "rating": 4.1, "maps_url": "https://maps.google.com"},
    {"name": "Sample Grill", "address": "789 Oak Rd", "rating": 3.9, "maps_url": "https://maps.google.com"},
]


@dataclass
class PlaceResult:
    name: str
    address: str
    rating: float
    maps_url: str

    def to_dict(self) -> dict:
        return {"name": self.name, "address": self.address, "rating": self.rating, "maps_url": self.maps_url}


class PlacesError(RuntimeError):
    pass


class PlacesAdapter:
    """Single seam for Places lookups. Pass empty api_key to force stub mode."""

    def __init__(self, api_key: str = "", radius_m: float = 2000.0, max_results: int = 5):
        self.api_key = api_key
        self.radius_m = radius_m
        self.max_results = max_results

    @property
    def stub_mode(self) -> bool:
        return not self.api_key

    async def search(self, query: str, fallback: str, lat: float, lng: float) -> list[dict]:
        """Run text search; if results sparse, retry with fallback. Returns up to max_results dicts."""
        if self.stub_mode:
            return list(_STUB_PLACES)

        async with httpx.AsyncClient() as client:
            results = await self._text(client, query, lat, lng)
            if len(results) < 3 and fallback:
                fb = await self._text(client, fallback, lat, lng)
                if len(fb) > len(results):
                    results = fb
        return results[: self.max_results]

    async def _text(self, client: httpx.AsyncClient, query: str, lat: float, lng: float) -> list[dict]:
        body = {
            "textQuery": query,
            "maxResultCount": self.max_results,
            "locationBias": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lng},
                    "radius": self.radius_m,
                }
            },
        }
        resp = await client.post(
            PLACES_URL,
            json=body,
            headers={
                "X-Goog-Api-Key": self.api_key,
                "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.googleMapsUri",
            },
        )
        if resp.status_code != 200:
            raise PlacesError(f"places API returned {resp.status_code}")
        data = resp.json()
        return [
            {
                "name": p.get("displayName", {}).get("text", ""),
                "address": p.get("formattedAddress", ""),
                "rating": p.get("rating", 0.0),
                "maps_url": p.get("googleMapsUri", ""),
            }
            for p in data.get("places", [])
        ]
