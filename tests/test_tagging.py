"""Tests for LLM tagging client with mocked Ollama responses."""

import json
from unittest.mock import patch, MagicMock

import pytest

from tagging.client import tag_food_item, parse_and_validate
from tests.mocks.ollama_responses import mock_ollama_response, MOCK_RESPONSES


class TestParseAndValidate:
    def test_valid_response(self):
        raw = json.dumps(MOCK_RESPONSES["Chicken Tikka Masala"])
        result = parse_and_validate(raw)
        assert result["spice_level"] == 0.5
        assert result["protein_type"] == "chicken"
        assert result["cuisine_type"] == "indian"
        assert result["carb_base"] == "rice"

    def test_clamps_values(self):
        raw = json.dumps({
            "spice_level": 1.5,
            "sweetness": -0.3,
            "protein_type": "chicken",
            "cuisine_type": "thai",
            "carb_base": "rice",
            "safety_flags": [],
            "dietary_flags": [],
        })
        result = parse_and_validate(raw)
        assert result["spice_level"] == 1.0
        assert result["sweetness"] == 0.0

    def test_invalid_protein_defaults_to_none(self):
        raw = json.dumps({
            "protein_type": "dragon_meat",
            "cuisine_type": "thai",
            "carb_base": "rice",
            "safety_flags": [],
            "dietary_flags": [],
        })
        result = parse_and_validate(raw)
        assert result["protein_type"] == "none"

    def test_invalid_cuisine_defaults_to_other(self):
        raw = json.dumps({
            "protein_type": "chicken",
            "cuisine_type": "martian",
            "carb_base": "rice",
            "safety_flags": [],
            "dietary_flags": [],
        })
        result = parse_and_validate(raw)
        assert result["cuisine_type"] == "other"

    def test_safety_bitmask_computed(self):
        raw = json.dumps(MOCK_RESPONSES["Spicy Tuna Roll"])
        result = parse_and_validate(raw)
        assert result["safety_risk_bitmask"] == 1  # raw_fish = bit 0

    def test_dietary_bitmask_computed(self):
        raw = json.dumps(MOCK_RESPONSES["Mac and Cheese"])
        result = parse_and_validate(raw)
        # vegetarian=bit0, contains_eggs=bit9 → 1 + 512 = 513
        assert result["dietary_flags_bitmask"] == 513

    def test_invalid_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            parse_and_validate("not json at all")


class TestTagFoodItem:
    @patch("tagging.client.requests.post")
    def test_calls_ollama_api(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_ollama_response("Chicken Tikka Masala")
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        result = tag_food_item("Chicken Tikka Masala", "Tender chicken in curry sauce")
        assert result["protein_type"] == "chicken"
        assert result["cuisine_type"] == "indian"
        mock_post.assert_called_once()

    @patch("tagging.client.requests.post")
    def test_handles_raw_fish_item(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_ollama_response("Spicy Tuna Roll")
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        result = tag_food_item("Spicy Tuna Roll")
        assert result["safety_risk_bitmask"] == 1  # raw_fish
        assert result["protein_type"] == "fish"

    @patch("tagging.client.requests.post")
    def test_unknown_item_gets_default(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_ollama_response("Mystery Dish")
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        result = tag_food_item("Mystery Dish")
        assert "spice_level" in result
        assert "protein_type" in result

    @patch("tagging.client.requests.post")
    def test_api_error_propagates(self, mock_post):
        mock_post.side_effect = ConnectionError("Ollama not running")
        with pytest.raises(ConnectionError):
            tag_food_item("Anything")
