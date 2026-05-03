"""Unit tests for PlacesAdapter — live code path (httpx mocked)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from places.adapter import PlacesAdapter, PlacesError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PLACES_3 = {
    "places": [
        {
            "displayName": {"text": "Ramen House"},
            "formattedAddress": "1 Main St, SF",
            "rating": 4.5,
            "googleMapsUri": "https://maps.google.com/?cid=1",
        },
        {
            "displayName": {"text": "Noodle Bar"},
            "formattedAddress": "2 Elm Ave, SF",
            "rating": 4.1,
            "googleMapsUri": "https://maps.google.com/?cid=2",
        },
        {
            "displayName": {"text": "Bowl & Broth"},
            "formattedAddress": "3 Oak Rd, SF",
            "rating": 3.9,
            "googleMapsUri": "https://maps.google.com/?cid=3",
        },
    ]
}

_PLACES_6 = {
    "places": [
        {
            "displayName": {"text": f"Place {i}"},
            "formattedAddress": f"{i} St",
            "rating": float(i),
            "googleMapsUri": f"https://maps.google.com/?cid={i}",
        }
        for i in range(1, 7)
    ]
}

_PLACES_1 = {
    "places": [
        {
            "displayName": {"text": "Lonely Bistro"},
            "formattedAddress": "99 Lone St",
            "rating": 3.5,
            "googleMapsUri": "https://maps.google.com/?cid=99",
        }
    ]
}

_PLACES_EMPTY = {"places": []}


def _mock_response(status_code: int, json_data: dict) -> MagicMock:
    r = MagicMock()
    r.status_code = status_code
    r.json.return_value = json_data
    return r


def _patch_client(*responses) -> tuple:
    """Patch httpx.AsyncClient to return successive mock responses on .post()."""
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=list(responses))
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=mock_client)
    cm.__aexit__ = AsyncMock(return_value=False)
    return patch("httpx.AsyncClient", return_value=cm), mock_client


# ---------------------------------------------------------------------------
# Stub mode
# ---------------------------------------------------------------------------

async def test_stub_mode_returns_stub_data():
    adapter = PlacesAdapter(api_key="")
    results = await adapter.search("ramen", "japanese restaurant", 37.77, -122.41)
    assert len(results) == 3
    assert all(k in results[0] for k in ("name", "address", "rating", "maps_url"))


async def test_stub_mode_no_http_calls():
    adapter = PlacesAdapter(api_key="")
    with patch("httpx.AsyncClient") as mock_cls:
        await adapter.search("ramen", "", 0.0, 0.0)
    mock_cls.assert_not_called()


# ---------------------------------------------------------------------------
# Live mode — happy path
# ---------------------------------------------------------------------------

async def test_live_happy_path():
    adapter = PlacesAdapter(api_key="test-key")
    patcher, mock_client = _patch_client(_mock_response(200, _PLACES_3))
    with patcher:
        results = await adapter.search("ramen", "japanese restaurant", 37.77, -122.41)
    assert len(results) == 3
    assert results[0]["name"] == "Ramen House"
    assert results[0]["address"] == "1 Main St, SF"
    assert results[0]["rating"] == 4.5
    assert "maps.google.com" in results[0]["maps_url"]


async def test_live_caps_at_max_results():
    adapter = PlacesAdapter(api_key="test-key", max_results=5)
    patcher, _ = _patch_client(_mock_response(200, _PLACES_6))
    with patcher:
        results = await adapter.search("ramen", "japanese restaurant", 37.77, -122.41)
    assert len(results) == 5


async def test_live_request_sends_correct_headers_and_body():
    adapter = PlacesAdapter(api_key="my-api-key", radius_m=1500.0, max_results=3)
    patcher, mock_client = _patch_client(_mock_response(200, _PLACES_3))
    with patcher:
        await adapter.search("pad thai", "thai restaurant", 40.71, -74.00)

    mock_client.post.assert_called_once()
    call_kwargs = mock_client.post.call_args
    headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers", {})
    body = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json", {})

    assert headers["X-Goog-Api-Key"] == "my-api-key"
    assert body["textQuery"] == "pad thai"
    assert body["locationBias"]["circle"]["center"]["latitude"] == 40.71
    assert body["locationBias"]["circle"]["radius"] == 1500.0


# ---------------------------------------------------------------------------
# Live mode — fallback logic
# ---------------------------------------------------------------------------

async def test_fallback_triggered_when_first_returns_few():
    """< 3 results on first call → retry with fallback query."""
    adapter = PlacesAdapter(api_key="test-key")
    patcher, mock_client = _patch_client(
        _mock_response(200, _PLACES_1),   # first call: 1 result
        _mock_response(200, _PLACES_3),   # fallback call: 3 results
    )
    with patcher:
        results = await adapter.search("pad thai", "thai restaurant", 37.77, -122.41)
    assert mock_client.post.call_count == 2
    assert len(results) == 3


async def test_fallback_not_triggered_when_first_has_enough():
    """≥ 3 results on first call → no fallback."""
    adapter = PlacesAdapter(api_key="test-key")
    patcher, mock_client = _patch_client(_mock_response(200, _PLACES_3))
    with patcher:
        results = await adapter.search("ramen", "japanese restaurant", 37.77, -122.41)
    assert mock_client.post.call_count == 1
    assert len(results) == 3


async def test_fallback_not_triggered_when_no_fallback_string():
    """Empty fallback string → no second call even if < 3 results."""
    adapter = PlacesAdapter(api_key="test-key")
    patcher, mock_client = _patch_client(_mock_response(200, _PLACES_1))
    with patcher:
        results = await adapter.search("pad thai", "", 37.77, -122.41)
    assert mock_client.post.call_count == 1
    assert len(results) == 1


async def test_fallback_not_used_when_primary_is_larger():
    """Fallback returns fewer results than primary → keep primary."""
    adapter = PlacesAdapter(api_key="test-key")
    patcher, mock_client = _patch_client(
        _mock_response(200, _PLACES_1),    # first call: 1 result
        _mock_response(200, {"places": []}),  # fallback: 0 results
    )
    with patcher:
        results = await adapter.search("pad thai", "thai restaurant", 37.77, -122.41)
    assert len(results) == 1


# ---------------------------------------------------------------------------
# Live mode — error handling
# ---------------------------------------------------------------------------

async def test_non_200_raises_places_error():
    adapter = PlacesAdapter(api_key="test-key")
    patcher, _ = _patch_client(_mock_response(403, {}))
    with patcher:
        with pytest.raises(PlacesError, match="403"):
            await adapter.search("ramen", "japanese restaurant", 37.77, -122.41)


async def test_empty_places_key_returns_empty_list():
    adapter = PlacesAdapter(api_key="test-key")
    patcher, _ = _patch_client(_mock_response(200, _PLACES_EMPTY))
    with patcher:
        results = await adapter.search("unicorn dish", "", 37.77, -122.41)
    assert results == []


async def test_missing_places_key_in_response():
    """API returns 200 but no 'places' field → empty list, no crash."""
    adapter = PlacesAdapter(api_key="test-key")
    patcher, _ = _patch_client(_mock_response(200, {}))
    with patcher:
        results = await adapter.search("ramen", "", 37.77, -122.41)
    assert results == []


async def test_missing_optional_fields_use_defaults():
    """Places entries missing rating/address/maps_url → graceful defaults."""
    sparse = {"places": [{"displayName": {"text": "Minimal Place"}}]}
    adapter = PlacesAdapter(api_key="test-key")
    patcher, _ = _patch_client(_mock_response(200, sparse))
    with patcher:
        results = await adapter.search("ramen", "", 37.77, -122.41)
    assert len(results) == 1
    assert results[0]["name"] == "Minimal Place"
    assert results[0]["address"] == ""
    assert results[0]["rating"] == 0.0
    assert results[0]["maps_url"] == ""


async def test_missing_display_name_uses_empty_string():
    """displayName field entirely absent → name defaults to empty string."""
    sparse = {"places": [{"formattedAddress": "1 Main St", "rating": 4.0}]}
    adapter = PlacesAdapter(api_key="test-key")
    patcher, _ = _patch_client(_mock_response(200, sparse))
    with patcher:
        results = await adapter.search("ramen", "", 37.77, -122.41)
    assert results[0]["name"] == ""
