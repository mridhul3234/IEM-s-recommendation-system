"""Turn a user query into a validated acoustic target profile."""

from __future__ import annotations

from collections import OrderedDict
import json
import logging
import os
import threading
import time

import pydantic

logger = logging.getLogger(__name__)

_PLACEHOLDER_PREFIXES = ("your_", "YOUR_", "placeholder_")
_PLACEHOLDER_EXACT = {"your_gemini_api_key_here"}
_MODELS_TO_TRY = ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-flash-latest"]
PROFILE_CACHE_TTL_SECONDS = 3600
PROFILE_CACHE_MAX_ENTRIES = 512
_profile_cache: OrderedDict[str, tuple[float, dict[str, float]]] = OrderedDict()
_profile_cache_lock = threading.RLock()

DEFAULT_PROFILE: dict[str, float] = {
    "sub_bass": 0.0, "bass": 0.0, "low_mids": 0.0, "mids": 0.0,
    "presence": 0.0, "treble": 0.0, "air": 0.0,
    "sibilance_risk": 0.0, "tonal_tilt": 0.0, "bass_to_treble": 0.0,
}


class TargetProfile(pydantic.BaseModel):
    sub_bass: float
    bass: float
    low_mids: float
    mids: float
    presence: float
    treble: float
    air: float
    sibilance_risk: float
    tonal_tilt: float
    bass_to_treble: float


PROMPT = """You are an audio engineering assistant. Convert this IEM search query into the requested acoustic target profile, relative to a neutral Harman target: {query!r}. Return only the schema values. Use 0.0 for unmentioned traits; do not invent product facts."""


def _is_real_key(api_key: str) -> bool:
    return bool(api_key) and api_key not in _PLACEHOLDER_EXACT and not api_key.startswith(_PLACEHOLDER_PREFIXES)


def call_gemini_api(prompt: str, api_key: str) -> str:
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=api_key)
    last_exc: Exception | None = None
    for model in _MODELS_TO_TRY:
        try:
            response = client.models.generate_content(
                model=model, contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json", response_schema=TargetProfile,
                    temperature=0.0,
                ),
            )
            return response.text
        except Exception as exc:
            logger.warning("Gemini model %s failed: %s", model, exc)
            last_exc = exc
    raise RuntimeError("All Gemini models failed") from last_exc


def parse_acoustic_json(json_str: str) -> dict[str, float]:
    """Parse and validate LLM output before any ranking code consumes it."""
    payload = json.loads(json_str)
    return TargetProfile.model_validate(payload).model_dump()


def _cache_key(query: str) -> str:
    return " ".join(query.casefold().split())


def _cache_get(key: str) -> dict[str, float] | None:
    now = time.monotonic()
    with _profile_cache_lock:
        cached = _profile_cache.get(key)
        if cached is None:
            return None
        expires_at, profile = cached
        if expires_at <= now:
            del _profile_cache[key]
            return None
        _profile_cache.move_to_end(key)
        return dict(profile)


def _cache_set(key: str, profile: dict[str, float]) -> None:
    with _profile_cache_lock:
        _profile_cache[key] = (time.monotonic() + PROFILE_CACHE_TTL_SECONDS, dict(profile))
        _profile_cache.move_to_end(key)
        while len(_profile_cache) > PROFILE_CACHE_MAX_ENTRIES:
            _profile_cache.popitem(last=False)


def infer_target_profile(query: str) -> dict[str, float]:
    """Use Gemini once per normalized query/hour; safely fall back to neutral."""
    key = _cache_key(query)
    if cached := _cache_get(key):
        return cached

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not _is_real_key(api_key):
        logger.warning("Gemini inference is unavailable; using a neutral target profile.")
        return dict(DEFAULT_PROFILE)

    try:
        profile = parse_acoustic_json(call_gemini_api(PROMPT.format(query=query), api_key))
    except Exception as exc:
        logger.warning("Gemini inference failed; using a neutral target profile: %s", exc)
        return dict(DEFAULT_PROFILE)
    _cache_set(key, profile)
    return profile
