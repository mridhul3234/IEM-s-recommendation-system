"""
infer.py

Parses a natural language user query into an inferred acoustic target profile
(the 7 bands + 3 derived features) using an LLM.
"""

import json
import os
import pydantic
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

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

PROMPT = """You are an audio engineering assistant. 
A user is searching for an IEM (in-ear monitor) based on the following free-text query:
"{query}"

Your task is to infer the target acoustic fingerprint that best matches their request.
The fingerprint represents the deviation from a neutral Harman target curve in decibels (dB), where 0.0 is completely neutral.

Features to infer:
- sub_bass (20-60Hz)
- bass (60-250Hz)
- low_mids (250-500Hz)
- mids (500-2000Hz)
- presence (2-6kHz)
- treble (6-10kHz)
- air (10-20kHz)
- sibilance_risk (0 to 10+): higher if they want sharp treble or explicitly want something bright, lower/zero if they want warm/smooth.
- tonal_tilt: negative for warm (bass-heavy), positive for bright (treble-heavy).
- bass_to_treble: positive if bassier than treble, negative if brighter.

If the user mentions specific traits (e.g. "heavy bass"), set those values accordingly (e.g. bass = 4.0).
If the user's query is vague (e.g. "something fun"), you might infer a mild V-shape (e.g. bass=2.0, treble=1.5).
If a trait is unmentioned, default to 0.0.

Respond strictly as a JSON object with the numerical float values. Do not include markdown formatting or backticks around the JSON.
"""

def call_gemini_api(prompt: str, api_key: str) -> str:
    """Attempts to call the Gemini API with a retry loop over different models."""
    models_to_try = ['gemini-2.0-flash', 'gemini-2.0-flash-lite', 'gemini-flash-latest']
    client = genai.Client(api_key=api_key)

    for model in models_to_try:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=TargetProfile,
                    temperature=0.0
                )
            )
            return response.text
        except Exception as e:
            print(f"Warning: Gemini API call failed with model {model}: {e}")
            continue
    raise Exception("All Gemini models failed")

def call_ollama_fallback(prompt: str) -> str:
    """Attempts to call a local Ollama server running Llama 3."""
    import requests
    payload = {
        "model": "llama3",
        "prompt": prompt,
        "format": "json",
        "stream": False
    }
    res = requests.post("http://localhost:11434/api/generate", json=payload, timeout=15)
    if res.status_code == 200:
        data = res.json()
        return data.get("response", "{}")
    raise Exception(f"Ollama returned status code {res.status_code}")

def parse_acoustic_json(json_str: str) -> dict[str, float]:
    """Parses JSON text safely into a dictionary."""
    return json.loads(json_str)

def infer_target_profile(query: str) -> dict[str, float]:
    """Infers the acoustic profile from a user query by orchestrating API calls."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    is_real_key = api_key and not api_key.startswith("your_") and not api_key.startswith("YOUR_") and api_key != "your_gemini_api_key_here"

    default_profile = {
        "sub_bass": 0.0, "bass": 0.0, "low_mids": 0.0, "mids": 0.0,
        "presence": 0.0, "treble": 0.0, "air": 0.0,
        "sibilance_risk": 0.0, "tonal_tilt": 0.0, "bass_to_treble": 0.0
    }
    
    prompt = PROMPT.format(query=query)

    if is_real_key:
        try:
            result_str = call_gemini_api(prompt, api_key)
            return parse_acoustic_json(result_str)
        except Exception as e:
            print(f"Warning: Gemini API call failed ({e}). Attempting Local Ollama Fallback...")
    else:
        print("Notice: GEMINI_API_KEY in .env is missing or set to placeholder. Please set your Gemini API key in .env.")

    try:
        result_str = call_ollama_fallback(prompt)
        return parse_acoustic_json(result_str)
    except Exception as e:
        print(f"Local Ollama fallback failed: {e}")

    print("All inference methods failed. Defaulting to neutral acoustic profile.")
    return default_profile
