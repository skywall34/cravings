"""Ollama client for food attribute tagging."""

import json

import numpy as np
import requests

from tagging.prompt import build_tagging_prompt
from tagging.safety import compute_safety_bitmask, compute_dietary_bitmask

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
MODEL = "gemma4:e2b"
EMBED_MODEL = "nomic-embed-text"

CONTINUOUS_FIELDS = [
    "spice_level", "sweetness", "sourness", "savory_umami", "saltiness", "bitterness",
    "temperature", "texture_softness", "sauce_heaviness", "richness",
    "veggie_density", "dairy_content", "smell_intensity", "nausea_trigger",
]
CATEGORICAL_FIELDS = ["protein_type", "cuisine_type", "carb_base"]
VALID_PROTEIN = {"chicken", "beef", "pork", "fish", "shellfish", "egg", "tofu_plant", "legume", "none"}
VALID_CUISINE = {
    "american", "mexican", "italian", "chinese", "japanese", "thai",
    "indian", "korean", "mediterranean", "middle_eastern",
    "french", "spanish", "german", "eastern_european",
    "vietnamese", "filipino", "indonesian", "brazilian", "caribbean", "ethiopian",
    "other",
}
VALID_CARB = {"rice", "noodles_pasta", "bread", "potato", "tortilla", "none"}


def get_embedding(text: str, ollama_url: str = OLLAMA_EMBED_URL) -> np.ndarray:
    resp = requests.post(ollama_url, json={"model": EMBED_MODEL, "prompt": text}, timeout=30)
    resp.raise_for_status()
    vec = np.array(resp.json()["embedding"], dtype=np.float32)
    vec /= np.linalg.norm(vec) + 1e-8
    return vec


def tag_food_item(name: str, description: str | None = None, ollama_url: str = OLLAMA_URL) -> dict:
    messages = build_tagging_prompt(name, description)
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.1},
    }
    resp = requests.post(ollama_url, json=payload, timeout=60)
    resp.raise_for_status()
    content = resp.json()["message"]["content"]
    return parse_and_validate(content)


def parse_and_validate(raw_json: str) -> dict:
    data = json.loads(raw_json)
    result = {}

    for field in CONTINUOUS_FIELDS:
        val = data.get(field)
        if val is not None:
            result[field] = max(0.0, min(1.0, float(val)))

    protein = data.get("protein_type", "none")
    result["protein_type"] = protein if protein in VALID_PROTEIN else "none"

    cuisine = data.get("cuisine_type", "other")
    result["cuisine_type"] = cuisine if cuisine in VALID_CUISINE else "other"

    carb = data.get("carb_base", "none")
    result["carb_base"] = carb if carb in VALID_CARB else "none"

    safety_flags = data.get("safety_flags", [])
    dietary_flags = data.get("dietary_flags", [])
    result["safety_risk_bitmask"] = compute_safety_bitmask(safety_flags)
    result["dietary_flags_bitmask"] = compute_dietary_bitmask(dietary_flags)

    return result
