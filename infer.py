"""
infer.py

Parses a natural language user query into an inferred acoustic target profile
(the 7 bands + 3 derived features) using an LLM.
"""

import json
import os
import pydantic
from google import genai
from google.genai import types

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

def infer_target_profile(query: str) -> dict[str, float]:
    """Infers the acoustic profile from a user query."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is missing. Cannot run LLM inference.")
        
    client = genai.Client(api_key=api_key)
    
    response = client.models.generate_content(
        model='gemini-flash-latest',
        contents=PROMPT.format(query=query),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=TargetProfile,
            temperature=0.0
        )
    )
    
    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        # Fallback to an all-zero dictionary if parsing fails
        print("Warning: LLM returned invalid JSON. Defaulting to neutral profile.")
        return {
            "sub_bass": 0.0, "bass": 0.0, "low_mids": 0.0, "mids": 0.0,
            "presence": 0.0, "treble": 0.0, "air": 0.0,
            "sibilance_risk": 0.0, "tonal_tilt": 0.0, "bass_to_treble": 0.0
        }
