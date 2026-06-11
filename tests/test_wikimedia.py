"""Tests for Wikimedia image lookup tiers and license filtering."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from tests.mocks.wikimedia_responses import (
    COMMONS_EXTMETA_CC_BY_SA,
    COMMONS_EXTMETA_REJECTED,
    COMMONS_SEARCH_MISS,
    SPARQL_TIER1_HIT,
    SPARQL_TIER1_MISS,
    WIKIPEDIA_PAGEIMAGE_HIT,
    WIKIPEDIA_PAGEIMAGE_MISS,
    WIKIPEDIA_PAGEIMAGE_THUMBNAIL_ENCODED,
)
from tagging.wikimedia import (
    fetch_metadata,
    find_image_tier1,
    find_image_tier2,
    find_image_tier3,
    find_image,
    find_image_candidates,
    _is_allowed_license,
    _normalize_license,
)


def _mock_client(*responses):
    """Build a mock httpx.Client that returns given responses in sequence."""
    client = MagicMock(spec=httpx.Client)
    mock_resps = []
    for r in responses:
        m = MagicMock()
        if r is None:
            # Simulate 404
            m.status_code = 404
            m.json.return_value = {"type": "https://mediawiki.org/wiki/HyperSwitch/errors/not_found"}
            m.raise_for_status = MagicMock()
        else:
            m.status_code = 200
            m.json.return_value = r
            m.raise_for_status = MagicMock()
        mock_resps.append(m)
    client.get.side_effect = mock_resps
    return client


class TestLicenseFilter:
    def test_cc_by_sa_4_allowed(self):
        assert _is_allowed_license("CC BY-SA 4.0")

    def test_cc_by_4_allowed(self):
        assert _is_allowed_license("CC BY 4.0")

    def test_cc0_allowed(self):
        assert _is_allowed_license("CC0")

    def test_public_domain_allowed(self):
        assert _is_allowed_license("Public domain")

    def test_all_rights_reserved_rejected(self):
        assert not _is_allowed_license("All rights reserved")

    def test_empty_rejected(self):
        assert not _is_allowed_license("")

    def test_normalize_cc_by_sa_4(self):
        assert _normalize_license("CC BY-SA 4.0") == "CC-BY-SA-4.0"

    def test_normalize_verbose_form(self):
        result = _normalize_license("Creative Commons Attribution-Share Alike 4.0")
        assert result == "CC-BY-SA-4.0"

    def test_locale_port_stripped_from_license(self):
        assert _is_allowed_license("CC BY-SA 2.0 kr")

    def test_locale_port_hyphen_form(self):
        assert _is_allowed_license("cc-by-sa-2.0-kr")

    def test_locale_strip_does_not_affect_public_domain(self):
        assert _is_allowed_license("Public Domain")


class TestFetchMetadata:
    def test_returns_attribution_for_cc_license(self):
        client = _mock_client(COMMONS_EXTMETA_CC_BY_SA)
        result = fetch_metadata("https://commons.wikimedia.org/wiki/File:Carbonara.jpg", client)
        assert result is not None
        assert result.license == "CC-BY-SA-4.0"
        assert result.author == "Jane Photographer"

    def test_returns_none_for_rejected_license(self):
        client = _mock_client(COMMONS_EXTMETA_REJECTED)
        result = fetch_metadata("https://commons.wikimedia.org/wiki/File:Foo.jpg", client)
        assert result is None


class TestTier1:
    def test_tier1_hit(self):
        client = _mock_client(SPARQL_TIER1_HIT)
        result = find_image_tier1("Carbonara", client)
        assert result is not None
        assert result.tier == 1
        assert result.review_needed is False
        assert "commons.wikimedia.org" in result.file_page or "File:" in result.file_page

    def test_tier1_miss(self):
        client = _mock_client(SPARQL_TIER1_MISS)
        result = find_image_tier1("UnknownDish12345", client)
        assert result is None


class TestTier2:
    def test_tier2_hit(self):
        # tier2 tries "{name} ({cuisine} dish)" then "{name} (dish)" — hit on first
        client = _mock_client(WIKIPEDIA_PAGEIMAGE_HIT)
        result = find_image_tier2("Carbonara", "italian", client)
        assert result is not None
        assert result.tier == 2
        assert result.review_needed is False

    def test_tier2_miss(self):
        # Both disambig attempts miss
        client = _mock_client(WIKIPEDIA_PAGEIMAGE_MISS, WIKIPEDIA_PAGEIMAGE_MISS)
        result = find_image_tier2("Nonexistent", "italian", client)
        assert result is None


class TestThumbnailFilenameExtraction:
    def test_thumbnail_url_extracts_original_filename(self):
        """Thumbnail URLs like .../thumb/x/xx/Original.jpg/800px-Original.jpg
        must resolve to the actual Commons filename, not the thumbnail name."""
        client = _mock_client(WIKIPEDIA_PAGEIMAGE_THUMBNAIL_ENCODED)
        result = find_image_tier3("Fried Rice", client)
        assert result is not None
        # Filename must be URL-decoded and point to the actual file, not the thumbnail
        assert "Koh_Mak,_Thailand,_Fried_rice.jpg" in result.file_page
        assert "3840px" not in result.file_page


class TestTier3:
    def test_tier3_hit_sets_review_needed(self):
        client = _mock_client(WIKIPEDIA_PAGEIMAGE_HIT)
        result = find_image_tier3("Carbonara", client)
        assert result is not None
        assert result.tier == 3
        assert result.review_needed is True

    def test_tier3_miss(self):
        client = _mock_client(WIKIPEDIA_PAGEIMAGE_MISS)
        result = find_image_tier3("Nonexistent", client)
        assert result is None


class TestFindImage:
    def test_returns_tier1_first(self):
        """When tier 1 hits, skip tier 2 and 3."""
        client = _mock_client(SPARQL_TIER1_HIT)
        with patch("tagging.wikimedia.time.sleep"):
            result = find_image("Carbonara", "italian", client)
        assert result is not None
        assert result.tier == 1

    def test_falls_through_to_tier2(self):
        """Tier 1 miss → tier 2 hit (first disambig attempt)."""
        client = _mock_client(SPARQL_TIER1_MISS, WIKIPEDIA_PAGEIMAGE_HIT)
        with patch("tagging.wikimedia.time.sleep"):
            result = find_image("Carbonara", "italian", client)
        assert result is not None
        assert result.tier == 2

    def test_falls_through_to_tier3(self):
        """Tier 1 miss + tier 2 misses + tier 2.5 miss → tier 3 hit (needs_review)."""
        # Tier 2 makes 2 calls: "{name} (cuisine dish)" + "{name} (dish)"
        # Tier 2.5 makes 1 call: Commons search (returns empty)
        client = _mock_client(
            SPARQL_TIER1_MISS,
            WIKIPEDIA_PAGEIMAGE_MISS, WIKIPEDIA_PAGEIMAGE_MISS,  # tier 2
            COMMONS_SEARCH_MISS,                                  # tier 2.5
            WIKIPEDIA_PAGEIMAGE_HIT,                              # tier 3
        )
        with patch("tagging.wikimedia.time.sleep"):
            result = find_image("SomeDish", "korean", client)
        assert result is not None
        assert result.tier == 3
        assert result.review_needed is True

    def test_returns_none_when_all_tiers_miss(self):
        client = _mock_client(
            SPARQL_TIER1_MISS,
            WIKIPEDIA_PAGEIMAGE_MISS, WIKIPEDIA_PAGEIMAGE_MISS,  # tier 2
            COMMONS_SEARCH_MISS,                                  # tier 2.5
            WIKIPEDIA_PAGEIMAGE_MISS,                             # tier 3
        )
        with patch("tagging.wikimedia.time.sleep"):
            result = find_image("NoSuchDish", "thai", client)
        assert result is None


class TestFindImageCandidates:
    def test_tier1_hit_included(self):
        client = _mock_client(
            SPARQL_TIER1_HIT,           # tier1 → 1 candidate
            WIKIPEDIA_PAGEIMAGE_MISS,   # tier2 cuisine
            WIKIPEDIA_PAGEIMAGE_MISS,   # tier2 plain
            COMMONS_SEARCH_MISS,        # tier2.5
            WIKIPEDIA_PAGEIMAGE_MISS,   # tier3
        )
        with patch("tagging.wikimedia.time.sleep"):
            candidates = find_image_candidates("Carbonara", "italian", client, max_candidates=6)
        assert len(candidates) == 1
        assert candidates[0].tier == 1

    def test_multi_tier_ordering(self):
        """tier1 + tier3 both hit → tier1 first."""
        client = _mock_client(
            SPARQL_TIER1_HIT,           # tier1 → 1 candidate
            WIKIPEDIA_PAGEIMAGE_MISS,   # tier2 cuisine
            WIKIPEDIA_PAGEIMAGE_MISS,   # tier2 plain
            COMMONS_SEARCH_MISS,        # tier2.5
            WIKIPEDIA_PAGEIMAGE_HIT,    # tier3 → 1 candidate
        )
        with patch("tagging.wikimedia.time.sleep"):
            candidates = find_image_candidates("Carbonara", "italian", client, max_candidates=6)
        assert len(candidates) == 2
        assert candidates[0].tier == 1
        assert candidates[1].tier == 3

    def test_dedup_by_file_page(self):
        """Same file_page returned by tier1 and tier3 → only appears once."""
        # Both tiers return the same commons URL
        same_hit = {
            "results": {
                "bindings": [
                    {"image": {"type": "uri",
                               "value": "http://commons.wikimedia.org/wiki/Special:FilePath/Carbonara.jpg"}}
                ]
            }
        }
        # WIKIPEDIA_PAGEIMAGE_HIT returns File:Carbonara.jpg too
        client = _mock_client(
            same_hit,                   # tier1 → file_page = File:Carbonara.jpg
            WIKIPEDIA_PAGEIMAGE_MISS,   # tier2 cuisine
            WIKIPEDIA_PAGEIMAGE_MISS,   # tier2 plain
            COMMONS_SEARCH_MISS,        # tier2.5
            WIKIPEDIA_PAGEIMAGE_HIT,    # tier3 → also Carbonara.jpg
        )
        with patch("tagging.wikimedia.time.sleep"):
            candidates = find_image_candidates("Carbonara", "italian", client, max_candidates=6)
        file_pages = [c.file_page for c in candidates]
        assert len(file_pages) == len(set(file_pages)), "duplicate file_pages found"

    def test_max_candidates_respected(self):
        client = _mock_client(
            SPARQL_TIER1_HIT,
            WIKIPEDIA_PAGEIMAGE_MISS,
            WIKIPEDIA_PAGEIMAGE_MISS,
            COMMONS_SEARCH_MISS,
            WIKIPEDIA_PAGEIMAGE_HIT,
        )
        with patch("tagging.wikimedia.time.sleep"):
            candidates = find_image_candidates("Carbonara", "italian", client, max_candidates=1)
        assert len(candidates) <= 1

    def test_find_image_still_returns_first(self):
        """find_image() wraps find_image_candidates(max=1) — backward compat."""
        client = _mock_client(SPARQL_TIER1_HIT)
        with patch("tagging.wikimedia.time.sleep"):
            result = find_image("Carbonara", "italian", client)
        assert result is not None
        assert result.tier == 1
