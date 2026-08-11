"""
describe.py

Turns a feature dict into a short natural-language tonal description using an LLM.
Includes an offline caching mechanism to avoid re-running the LLM for unchanged
feature vectors.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """\
You are an audio reviewer describing an IEM's tonal character from measured \
frequency-response data. Do not mention numbers or dB values in your answer \
-- translate them into the kind of plain, sensory language a listener would use.

Measured deviation from a neutral (Harman) target, by band, in dB:
- Sub-bass (20-60 Hz):   {sub_bass}
- Bass (60-250 Hz):      {bass}
- Low-mids (250-500 Hz): {low_mids}
- Mids (500-2000 Hz):    {mids}
- Presence (2-6 kHz):    {presence}
- Treble (6-10 kHz):     {treble}
- Air (10-20 kHz):       {air}
Sibilance risk score (0 = none, higher = sharper/harsher): {sibilance_risk}
Overall tonal tilt (negative = warm, positive = bright): {tonal_tilt}

Write 1-2 sentences describing the tonal signature, suitable for someone \
searching for an IEM by vibe rather than by spec.\
"""

_CACHE_FILE = "descriptions_cache.json"
_PLACEHOLDER_PREFIXES = ("your_", "YOUR_")
_FALLBACK_MODEL = "gemini-flash-latest"


def _hash_features(features: dict[str, float]) -> str:
    stable_repr = json.dumps(features, sort_keys=True)
    return hashlib.md5(stable_repr.encode("utf-8")).hexdigest()


def _load_cache() -> dict[str, str]:
    if os.path.exists(_CACHE_FILE):
        with open(_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cache(cache: dict[str, str]) -> None:
    with open(_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)


def _is_real_key(api_key: str) -> bool:
    return bool(api_key) and not any(
        api_key.startswith(p) for p in _PLACEHOLDER_PREFIXES
    )


def describe(features: dict[str, float], iem_name: str = "Unknown") -> str:
    """
    Return a 1-2 sentence tonal description for an IEM.

    Checks the local cache first. If a miss, calls Gemini (when a valid
    API key is present) and caches the result. Falls back to a generic
    description when no key is available.
    """
    cache = _load_cache()
    cache_key = f"{iem_name}_{_hash_features(features)}"

    if cache_key in cache:
        return cache[cache_key]

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not _is_real_key(api_key):
        logger.info(
            "No valid GEMINI_API_KEY — using fallback description for %s.", iem_name
        )
        return (
            f"{iem_name} is a balanced, high-resolution in-ear monitor "
            "tuned against standardised acoustic targets."
        )

    # Lazy import — avoid loading library startup cost when cache is hit.
    from google import genai

    client = genai.Client(api_key=api_key)
    prompt = PROMPT_TEMPLATE.format(**features)

    try:
        response = client.models.generate_content(
            model=_FALLBACK_MODEL,
            contents=prompt,
        )
        desc = response.text.strip()
    except Exception as exc:
        logger.warning("Gemini describe call failed for %s: %s", iem_name, exc)
        return (
            f"{iem_name} is a balanced, high-resolution in-ear monitor "
            "tuned against standardised acoustic targets."
        )

    cache[cache_key] = desc
    _save_cache(cache)
    return desc
