"""
describe.py

Turns a feature dict into a short natural-language tonal description.

This file is a RULE-BASED STAND-IN for the LLM step in the full design.
It exists so the pipeline is fully runnable end-to-end right now, without
an API key, and so you can unit-test the embedding/search step against
consistent, deterministic text before variance from an LLM enters the
picture.

When you're ready to add the real LLM step, replace `describe()` below
with a call like:

    prompt = PROMPT_TEMPLATE.format(**features)
    response = client.messages.create(
        model="claude-...",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )

...and use the model's prose instead. Keep PROMPT_TEMPLATE below as your
starting point -- it's already shaped to the exact feature dict this
module produces.
"""

from __future__ import annotations

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


def describe(features: dict[str, float]) -> str:
    """Deterministic, threshold-based description. Same shape of output
    as what the LLM prompt above should eventually produce."""
    parts = []

    if features["bass"] > 4:
        parts.append("heavy, elevated bass")
    elif features["bass"] > 1.5:
        parts.append("warm, present bass")
    elif features["bass"] < -2:
        parts.append("lean, reserved bass")
    else:
        parts.append("neutral bass")

    if features["mids"] > 2:
        parts.append("forward, present vocals")
    elif features["mids"] < -2:
        parts.append("recessed, laid-back mids")

    if features["sibilance_risk"] > 3:
        parts.append("a noticeable sibilance peak in the treble")
    elif features["sibilance_risk"] > 1.2:
        parts.append("mild treble sharpness")

    if features["tonal_tilt"] < -1.5:
        parts.append("an overall warm, smooth tonal tilt")
    elif features["tonal_tilt"] > 1.5:
        parts.append("an overall bright, energetic tonal tilt")

    if features["air"] > 2:
        parts.append("extended, airy top end")
    elif features["air"] < -3:
        parts.append("rolled-off upper treble")

    if not parts:
        return "A fairly neutral, balanced tonal signature."
    return ("Has " + ", ".join(parts) + ".").replace(", .", ".")
