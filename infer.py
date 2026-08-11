"""
infer.py

Parses a natural language user query into an inferred acoustic target profile
(the 7 bands + 3 derived features) using a Gemini LLM, with a local Ollama
fallback and a neutral-profile final fallback.
"""

import json
import logging
import os
import pydantic
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

logger = logging.getLogger(__name__)

_PLACEHOLDER_PREFIXES = ("your_", "YOUR_")
_PLACEHOLDER_EXACT = {"your_gemini_api_key_here"}
_MODELS_TO_TRY = ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-flash-latest"]

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


PROMPT = """\
You are an audio engineering assistant.
A user is searching for an IEM (in-ear monitor) based on the following free-text query:
"{query}"

Your task is to infer the target acoustic fingerprint that best matches their request.
The fingerprint represents the deviation from a neutral Harman target curve in decibels (dB), \
where 0.0 is completely neutral.

Features to infer:
- sub_bass (20-60 Hz)
- bass (60-250 Hz)
- low_mids (250-500 Hz)
- mids (500-2000 Hz)
- presence (2-6 kHz)
- treble (6-10 kHz)
- air (10-20 kHz)
- sibilance_risk (0 to 10+): higher if they want sharp treble or explicitly want something bright, \
lower/zero if they want warm/smooth.
- tonal_tilt: negative for warm (bass-heavy), positive for bright (treble-heavy).
- bass_to_treble: positive if bassier than treble, negative if brighter.

If the user mentions specific traits (e.g. "heavy bass"), set those values accordingly \
(e.g. bass = 4.0).
If the user's query is vague (e.g. "something fun"), you might infer a mild V-shape \
(e.g. bass=2.0, treble=1.5).
If a trait is unmentioned, default to 0.0.

Respond strictly as a JSON object with numerical float values. \
Do not include markdown formatting or backticks.
"""


def _is_real_key(api_key: str) -> bool:
    if not api_key:
        return False
    if api_key in _PLACEHOLDER_EXACT:
        return False
    if any(api_key.startswith(p) for p in _PLACEHOLDER_PREFIXES):
        return False
    return True


def call_gemini_api(prompt: str, api_key: str) -> str:
    """Try each model in sequence; raise if all fail."""
    client = genai.Client(api_key=api_key)

    last_exc: Exception | None = None
    for model in _MODELS_TO_TRY:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=TargetProfile,
                    temperature=0.0,
                ),
            )
            return response.text
        except Exception as exc:
            logger.warning("Gemini model %s failed: %s", model, exc)
            last_exc = exc

    raise Exception("All Gemini models failed") from last_exc


def call_ollama_fallback(prompt: str) -> str:
    """Call a local Ollama server running Llama 3."""
    import requests
    payload = {
        "model": "llama3",
        "prompt": prompt,
        "format": "json",
        "stream": False,
    }
    res = requests.post("http://localhost:11434/api/generate", json=payload, timeout=15)
    if res.status_code == 200:
        return res.json().get("response", "{}")
    raise Exception(f"Ollama returned status {res.status_code}")


def parse_acoustic_json(json_str: str) -> dict[str, float]:
    """Parse JSON string into a feature dict."""
    return json.loads(json_str)


def infer_target_profile(query: str) -> dict[str, float]:
    """
    Infer the acoustic profile from a user query.
    Falls back through: Gemini → Ollama → neutral default profile.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    prompt = PROMPT.format(query=query)

    if _is_real_key(api_key):
        try:
            return parse_acoustic_json(call_gemini_api(prompt, api_key))
        except Exception as exc:
            logger.warning("Gemini failed (%s). Trying Ollama...", exc)
    else:
        logger.info(
            "GEMINI_API_KEY not set or is a placeholder. "
            "Set a real key in .env to enable LLM inference."
        )

    try:
        return parse_acoustic_json(call_ollama_fallback(prompt))
    except Exception as exc:
        logger.warning("Ollama fallback failed: %s", exc)

    logger.warning("All inference methods failed. Defaulting to neutral acoustic profile.")
    return dict(DEFAULT_PROFILE)
