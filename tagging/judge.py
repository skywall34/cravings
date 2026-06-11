"""VLM image judge — validates food photos via local Ollama gemma4:e2b."""

import base64
import io
import json
from dataclasses import dataclass
from pathlib import Path

import requests
from PIL import Image

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
MODEL = "gemma4:e2b"

_SYSTEM_PROMPT = (
    "You are a food photo validator. Given an image and a dish name, decide if the image "
    "is a plausible photograph of that dish.\n\n"
    "FAIL immediately if the image is:\n"
    "- Not a photograph (painting, drawing, illustration, logo, map, diagram)\n"
    "- Contains no prepared food (raw ingredients only, empty plate, non-food object)\n"
    "- Clearly the wrong food category (e.g. a dessert shown for a savory dish)\n\n"
    "PASS if the image plausibly depicts the dish, including look-alike dishes, "
    "different presentations, or close variants. When unsure, PASS.\n\n"
    'Respond ONLY with JSON: {"verdict": "pass" or "fail", "reason": "<20 words max>"}'
)


class JudgeError(Exception):
    """Raised when judge cannot produce a verdict (Ollama down, unparsable response)."""


@dataclass
class Verdict:
    verdict: str  # "pass" or "fail"
    reason: str


def prepare_image(image_bytes: bytes, max_side: int = 896) -> str:
    """Downscale to max_side, re-encode as JPEG, return base64 string."""
    Image.MAX_IMAGE_PIXELS = None  # large Wikimedia originals are not attacks
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    w, h = img.size
    if max(w, h) > max_side:
        scale = max_side / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


def parse_verdict(raw: str) -> Verdict:
    """Parse VLM JSON response. Raises JudgeError on garbage/unknown verdict."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise JudgeError(f"JSON parse failed: {e}") from e

    verdict = str(data.get("verdict", "")).strip().lower()
    if verdict not in ("pass", "fail"):
        raise JudgeError(f"Unknown verdict: {verdict!r}")

    reason = str(data.get("reason", "")).strip()
    return Verdict(verdict=verdict, reason=reason)


def judge_image_bytes(
    image_bytes: bytes,
    dish_name: str,
    ollama_url: str = OLLAMA_URL,
) -> Verdict:
    """Judge raw image bytes for a named dish. Raises JudgeError on failure."""
    b64 = prepare_image(image_bytes)
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Dish: {dish_name}",
                "images": [b64],
            },
        ],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0},
    }
    try:
        resp = requests.post(ollama_url, json=payload, timeout=120)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise JudgeError(f"Ollama request failed: {e}") from e

    content = resp.json()["message"]["content"]
    return parse_verdict(content)


def judge_image_file(
    path: Path,
    dish_name: str,
    ollama_url: str = OLLAMA_URL,
) -> Verdict:
    """Judge an image file on disk. Raises JudgeError on failure."""
    return judge_image_bytes(path.read_bytes(), dish_name, ollama_url=ollama_url)


def check_ollama_available(tags_url: str = OLLAMA_TAGS_URL) -> bool:
    """Return True if Ollama is reachable."""
    try:
        resp = requests.get(tags_url, timeout=5)
        return resp.status_code == 200
    except requests.RequestException:
        return False
