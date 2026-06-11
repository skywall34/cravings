"""Tests for Openverse image search."""

from unittest.mock import MagicMock

import httpx
import pytest

from tests.mocks.openverse_responses import (
    OPENVERSE_RESULTS_CC_BY_SA,
    OPENVERSE_RESULTS_EMPTY,
    OPENVERSE_RESULTS_PDM,
    OPENVERSE_RESULTS_UNLICENSED,
)
from tagging.openverse import search_openverse


def _mock_client(response_data: dict, status_code: int = 200) -> httpx.Client:
    client = MagicMock(spec=httpx.Client)
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = response_data
    mock_resp.raise_for_status = MagicMock()
    client.get.return_value = mock_resp
    return client


class TestSearchOpenverse:
    def test_returns_results_for_allowed_licenses(self):
        client = _mock_client(OPENVERSE_RESULTS_CC_BY_SA)
        results = search_openverse("carbonara italian dish", client)
        assert len(results) == 2
        assert results[0].license == "CC-BY-SA-4.0"
        assert results[1].license == "CC0"

    def test_drops_non_allowlisted_license(self):
        client = _mock_client(OPENVERSE_RESULTS_UNLICENSED)
        results = search_openverse("some dish", client)
        assert len(results) == 0

    def test_empty_results(self):
        client = _mock_client(OPENVERSE_RESULTS_EMPTY)
        results = search_openverse("obscure dish", client)
        assert results == []

    def test_pdm_maps_to_pd(self):
        client = _mock_client(OPENVERSE_RESULTS_PDM)
        results = search_openverse("old dish", client)
        assert len(results) == 1
        assert results[0].license == "PD"

    def test_attribution_mapping(self):
        client = _mock_client(OPENVERSE_RESULTS_CC_BY_SA)
        results = search_openverse("carbonara", client)
        assert results[0].creator == "Chef Photo"
        assert results[0].foreign_landing_url == "https://openverse.example.com/food1"
        assert results[0].url == "https://openverse.example.com/food1.jpg"

    def test_missing_creator_defaults_to_unknown(self):
        client = _mock_client(OPENVERSE_RESULTS_PDM)
        results = search_openverse("old dish", client)
        assert results[0].creator == "Unknown"

    def test_limit_respected(self):
        client = _mock_client(OPENVERSE_RESULTS_CC_BY_SA)
        results = search_openverse("food", client, limit=1)
        assert len(results) == 1

    def test_request_error_returns_empty(self):
        client = MagicMock(spec=httpx.Client)
        client.get.side_effect = httpx.RequestError("connection refused", request=MagicMock())
        results = search_openverse("spaghetti", client)
        assert results == []
