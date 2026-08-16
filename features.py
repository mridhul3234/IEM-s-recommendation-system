"""
features.py

Turns a (frequency, deviation_db) curve -- the output of
normalize.deviation_from_target -- into a small, interpretable feature
vector. This is the "acoustic fingerprint" that everything downstream
(the LLM description step, the embedding, the explainability overlay)
is built from.

Design choice: instead of embedding the raw ~300-point curve directly,
we first collapse it into named frequency bands. Two reasons:
  1. Interpretability -- "this IEM has +4.2 dB in the bass band" is
     something you can show on a chart and explain in an interview.
     A raw 300-dim vector is not.
  2. It's the same representation an LLM prompt needs anyway, since you
     can't usefully hand a language model 300 raw numbers and expect
     good prose back -- but "+4.2 dB bass, -1.1 dB presence, sibilance
     risk 0.3" is exactly the kind of compact summary a prompt template
     can turn into natural language reliably.
"""

from __future__ import annotations

import numpy as np

# Band boundaries in Hz. These follow common audio-engineering convention
# (sub-bass / bass / low-mids / mids / presence / treble / air) rather than
# anything IEM-specific -- feel free to tighten these once you've looked at
# enough curves to have opinions.
BANDS = {
    "sub_bass": (20, 60),
    "bass": (60, 250),
    "low_mids": (250, 500),
    "mids": (500, 2000),
    "presence": (2000, 6000),
    "treble": (6000, 10000),
    "air": (10000, 20000),
}

# Sibilance lives in a narrower window than the full presence/treble split
# above -- a sharp peak here (not just an overall rise) is what makes
# "s" and "sh" sounds and cymbals splashy/harsh.
SIBILANCE_BAND = (5000, 9000)


def _band_mask(freq: np.ndarray, lo: float, hi: float) -> np.ndarray:
    return (freq >= lo) & (freq < hi)


def band_averages(freq: np.ndarray, deviation_db: np.ndarray) -> dict[str, float]:
    """Mean deviation-from-target within each named band, in dB."""
    out = {}
    for name, (lo, hi) in BANDS.items():
        mask = _band_mask(freq, lo, hi)
        out[name] = float(np.mean(deviation_db[mask])) if mask.any() else 0.0
    return out


def sibilance_risk(freq: np.ndarray, deviation_db: np.ndarray) -> float:
    """Peak deviation within the sibilance window, relative to the local
    presence-band baseline. A tall, narrow peak here scores high; a curve
    that's just generally forward through the mids/presence does not,
    because it's the *peak above baseline*, not the absolute level, that
    correlates with perceived sibilance.
    
    Recalibrated: If the absolute peak is below neutral (0 dB), it is
    not perceived as sibilant regardless of the relative jump."""
    mask = _band_mask(freq, *SIBILANCE_BAND)
    if not mask.any():
        return 0.0
    baseline = float(np.mean(deviation_db[_band_mask(freq, 2000, 5000)]))
    peak = float(np.max(deviation_db[mask]))
    
    if peak <= 0:
        return 0.0
        
    return round(max(0.0, peak - baseline), 2)


def tonal_tilt(freq: np.ndarray, deviation_db: np.ndarray) -> float:
    """Overall warm<->bright tilt, as the slope of a linear fit of
    deviation vs log-frequency. Negative = tilts warm (bass-forward,
    treble recessed relative to target); positive = tilts bright."""
    log_f = np.log10(freq)
    slope, _ = np.polyfit(log_f, deviation_db, 1)
    return round(float(slope), 3)


def bass_to_treble_ratio(bands: dict[str, float]) -> float:
    """Simple, very legible summary: how much more (or less) bass than
    treble this IEM has relative to target, in dB. Positive = bassier
    than the target's balance; negative = brighter."""
    return round(bands["bass"] - bands["treble"], 2)


def extract_features(freq: np.ndarray, deviation_db: np.ndarray) -> dict[str, float]:
    """Full feature dict for one IEM: 7 band averages + 3 derived signals.
    This dict is the thing that (a) drives the LLM description prompt,
    (b) gets shown in the explainability overlay, and (c) can be turned
    into a fixed-order vector for a hybrid acoustic-similarity re-rank
    alongside the text embedding similarity.
    """
    bands = band_averages(freq, deviation_db)
    features = {**bands}
    features["sibilance_risk"] = sibilance_risk(freq, deviation_db)
    features["tonal_tilt"] = tonal_tilt(freq, deviation_db)
    features["bass_to_treble"] = bass_to_treble_ratio(bands)
    return {k: round(v, 2) if isinstance(v, float) else v for k, v in features.items()}


FEATURE_ORDER = list(BANDS.keys()) + ["sibilance_risk", "tonal_tilt", "bass_to_treble"]


def validate_feature_profile(features: dict[str, float]) -> dict[str, float]:
    """Validate the complete numeric acoustic profile before vectorization."""
    if not isinstance(features, dict):
        raise ValueError("Acoustic profile must be an object.")

    validated: dict[str, float] = {}
    for key in FEATURE_ORDER:
        if key not in features:
            raise ValueError(f"Acoustic profile is missing required feature '{key}'.")
        try:
            value = float(features[key])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Acoustic profile feature '{key}' must be numeric.") from exc
        if not np.isfinite(value):
            raise ValueError(f"Acoustic profile feature '{key}' must be finite.")
        validated[key] = value
    return validated


def to_vector(features: dict[str, float]) -> np.ndarray:
    """Fixed-order numpy vector, for the hybrid acoustic-distance re-rank
    step (cosine or euclidean distance between two IEMs' fingerprints)."""
    profile = validate_feature_profile(features)
    return np.array([profile[k] for k in FEATURE_ORDER], dtype=float)
