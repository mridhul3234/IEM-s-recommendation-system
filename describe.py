"""
describe.py

Turns a feature dict into a short natural-language tonal description using an LLM.
Includes an offline caching mechanism to avoid re-running the LLM for unchanged
feature vectors.
"""

from __future__ import annotations

import json
import os
import hashlib

PROMPT_TEMPLATE = """You are an audio reviewer describing an IEM's tonal \
character from measured frequency-response data. Do not mention numbers \
or dB values in your answer -- translate them into the kind of plain, \
sensory language a listener would use.

Measured deviation from a neutral (Harman) target, by band, in dB:
- Sub-bass (20-60Hz): {sub_bass}
- Bass (60-250Hz): {bass}
- Low-mids (250-500Hz): {low_mids}
- Mids (500-2000Hz): {mids}
- Presence (2-6kHz): {presence}
- Treble (6-10kHz): {treble}
- Air (10-20kHz): {air}
Sibilance risk score (0 = none, higher = sharper/harsher): {sibilance_risk}
Overall tonal tilt (negative = warm, positive = bright): {tonal_tilt}

Write 1-2 sentences describing the tonal signature, suitable for someone \
searching for an IEM by vibe rather than by spec."""

CACHE_FILE = "descriptions_cache.json"

def _hash_features(features: dict[str, float]) -> str:
    # Sort keys for deterministic hashing
    stable_repr = json.dumps(features, sort_keys=True)
    return hashlib.md5(stable_repr.encode("utf-8")).hexdigest()

def _load_cache() -> dict[str, str]:
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def _save_cache(cache: dict[str, str]):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

def describe(features: dict[str, float], iem_name: str = "Unknown") -> str:
    """LLM-based description. Checks a local cache first."""
    cache = _load_cache()
    
    # Key is IEM name + hash of the features
    feat_hash = _hash_features(features)
    cache_key = f"{iem_name}_{feat_hash}"
    
    if cache_key in cache:
        return cache[cache_key]
        
    # Lazy import to avoid loading the library if we hit the cache
    from google import genai
    
    # Ensure the API key is set
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is missing. Cannot generate new description.")
        
    client = genai.Client(api_key=api_key)
    
    prompt = PROMPT_TEMPLATE.format(**features)
    
    response = client.models.generate_content(
        model='gemini-flash-latest',
        contents=prompt
    )
    desc = response.text.strip()
    
    cache[cache_key] = desc
    _save_cache(cache)
    
    return desc
