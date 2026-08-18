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
from pathlib import Path
import tempfile
from contextlib import contextmanager

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

_CACHE_FILE = Path(__file__).resolve().with_name("descriptions_cache.json")
_LOCK_FILE = _CACHE_FILE.with_suffix(".lock")
_PLACEHOLDER_PREFIXES = ("your_", "YOUR_")
_FALLBACK_MODEL = "gemini-flash-latest"


def _hash_features(features: dict[str, float]) -> str:
    stable_repr = json.dumps(features, sort_keys=True)
    return hashlib.md5(stable_repr.encode("utf-8")).hexdigest()


def _load_cache() -> dict[str, str]:
    if _CACHE_FILE.exists():
        try:
            with _CACHE_FILE.open("r", encoding="utf-8") as f:
                cache = json.load(f)
            if not isinstance(cache, dict):
                raise ValueError("cache root is not an object")
            return {key: value for key, value in cache.items() if isinstance(key, str) and isinstance(value, str)}
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            logger.warning("Ignoring unreadable description cache: %s", exc)
    return {}


@contextmanager
def _file_lock():
    """Synchronize cache writes across workers and protect concurrent readers."""
    _LOCK_FILE.touch(exist_ok=True)
    with _LOCK_FILE.open("a+") as lock_handle:
        if os.name == "nt":
            import msvcrt
            lock_handle.seek(0)
            lock_handle.write("0")
            lock_handle.flush()
            msvcrt.locking(lock_handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if os.name == "nt":
                lock_handle.seek(0)
                msvcrt.locking(lock_handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)


def _save_cache(cache: dict[str, str]) -> None:
    _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=_CACHE_FILE.parent, delete=False) as f:
        json.dump(cache, f, indent=2)
        temp_name = f.name
    os.replace(temp_name, _CACHE_FILE)


def _merge_and_save(entries: dict[str, str]) -> None:
    if not entries:
        return
    with _file_lock():
        cache = _load_cache()
        cache.update(entries)
        _save_cache(cache)


def _is_real_key(api_key: str) -> bool:
    return bool(api_key) and not any(
        api_key.startswith(p) for p in _PLACEHOLDER_PREFIXES
    )


def _describe(features: dict[str, float], iem_name: str, cache: dict[str, str]) -> tuple[str, str | None]:
    cache_key = f"{iem_name}_{_hash_features(features)}"
    if cache_key in cache:
        return cache[cache_key], None
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not _is_real_key(api_key):
        logger.info("No valid GEMINI_API_KEY — using fallback description for %s.", iem_name)
        return "Measured frequency-response profile, shown relative to the Harman target.", None
    from google import genai
    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(model=_FALLBACK_MODEL, contents=PROMPT_TEMPLATE.format(**features))
        desc = response.text.strip()
    except Exception as exc:
        logger.warning("Gemini describe call failed for %s: %s", iem_name, exc)
        return "Measured frequency-response profile, shown relative to the Harman target.", None
    cache[cache_key] = desc
    return desc, cache_key


def describe_many(items: list[tuple[dict[str, float], str]]) -> list[str]:
    """Describe an ingestion batch with one cache read and, at most, one write."""
    cache = _load_cache()
    new_entries: dict[str, str] = {}
    descriptions: list[str] = []
    for features, iem_name in items:
        description, cache_key = _describe(features, iem_name, cache)
        descriptions.append(description)
        if cache_key:
            new_entries[cache_key] = description
    _merge_and_save(new_entries)
    return descriptions


def describe(features: dict[str, float], iem_name: str = "Unknown") -> str:
    """Return a cached or newly generated description for one IEM."""
    return describe_many([(features, iem_name)])[0]
