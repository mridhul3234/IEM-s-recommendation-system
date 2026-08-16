"""
tests/test_features.py

Unit tests for features.py — band averaging, sibilance risk,
tonal tilt, and to_vector. These test pure math with no I/O or
network dependencies, so they must be fully hermetic.
"""

import numpy as np
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from features import (
    band_averages, sibilance_risk, tonal_tilt,
    bass_to_treble_ratio, extract_features, to_vector,
    FEATURE_ORDER, BANDS
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def flat_curve(value: float = 0.0, n: int = 300) -> tuple:
    """Return a log-spaced freq grid + a flat deviation curve."""
    freq = np.logspace(np.log10(20), np.log10(20000), n)
    db = np.full(n, value)
    return freq, db


def shaped_curve(n: int = 300) -> tuple:
    """Sub-bass +6, bass +4, everything else 0."""
    freq = np.logspace(np.log10(20), np.log10(20000), n)
    db = np.zeros(n)
    db[freq < 60] = 6.0
    db[(freq >= 60) & (freq < 250)] = 4.0
    return freq, db


# ---------------------------------------------------------------------------
# band_averages
# ---------------------------------------------------------------------------

class TestBandAverages:
    def test_flat_neutral_curve(self):
        freq, db = flat_curve(0.0)
        avgs = band_averages(freq, db)
        for k in BANDS:
            assert avgs[k] == pytest.approx(0.0, abs=1e-6), f"Expected 0 for {k}"

    def test_flat_positive_curve(self):
        freq, db = flat_curve(3.0)
        avgs = band_averages(freq, db)
        for k in BANDS:
            assert avgs[k] == pytest.approx(3.0, abs=0.1), f"Expected 3.0 for {k}"

    def test_shaped_bass_boost(self):
        freq, db = shaped_curve()
        avgs = band_averages(freq, db)
        assert avgs["sub_bass"] > 4.0
        assert avgs["bass"] > 3.0
        assert avgs["mids"] == pytest.approx(0.0, abs=0.5)

    def test_returns_all_bands(self):
        freq, db = flat_curve()
        avgs = band_averages(freq, db)
        assert set(avgs.keys()) == set(BANDS.keys())

    def test_empty_band_returns_zero(self):
        # Very short freq array that might miss a band
        freq = np.array([1000.0, 1100.0, 1200.0])
        db = np.array([2.0, 2.0, 2.0])
        avgs = band_averages(freq, db)
        # sub_bass band (20-60 Hz) should have no points → 0.0
        assert avgs["sub_bass"] == 0.0


# ---------------------------------------------------------------------------
# sibilance_risk
# ---------------------------------------------------------------------------

class TestSibilanceRisk:
    def test_neutral_curve_is_zero(self):
        freq, db = flat_curve(0.0)
        assert sibilance_risk(freq, db) == pytest.approx(0.0)

    def test_negative_peak_is_zero(self):
        """If the sibilance band peak is below 0 dB, risk should be 0."""
        freq, db = flat_curve(-3.0)
        assert sibilance_risk(freq, db) == pytest.approx(0.0)

    def test_sharp_sibilance_spike(self):
        freq = np.logspace(np.log10(20), np.log10(20000), 300)
        db = np.zeros(300)
        # Spike at ~7 kHz (in 5k-9k window) well above baseline
        db[(freq >= 6500) & (freq < 8000)] = 10.0
        risk = sibilance_risk(freq, db)
        assert risk > 5.0

    def test_broad_elevated_presence_not_sibilant(self):
        """Overall presence lift without narrow spike should score low."""
        freq = np.logspace(np.log10(20), np.log10(20000), 300)
        db = np.zeros(300)
        db[freq >= 2000] = 2.0  # uniform 2 dB lift
        risk = sibilance_risk(freq, db)
        # peak - baseline ≈ 0 since they're equal
        assert risk < 0.5


# ---------------------------------------------------------------------------
# tonal_tilt
# ---------------------------------------------------------------------------

class TestTonalTilt:
    def test_neutral_flat_is_near_zero(self):
        freq, db = flat_curve(0.0)
        tilt = tonal_tilt(freq, db)
        assert abs(tilt) < 0.1

    def test_bass_heavy_is_negative(self):
        freq = np.logspace(np.log10(20), np.log10(20000), 300)
        db = np.linspace(6, -6, 300)  # descends from bass to air
        tilt = tonal_tilt(freq, db)
        assert tilt < 0

    def test_bright_is_positive(self):
        freq = np.logspace(np.log10(20), np.log10(20000), 300)
        db = np.linspace(-6, 6, 300)  # rises from bass to air
        tilt = tonal_tilt(freq, db)
        assert tilt > 0


# ---------------------------------------------------------------------------
# bass_to_treble_ratio
# ---------------------------------------------------------------------------

class TestBassToTreble:
    def test_equal_bands_is_zero(self):
        bands = {k: 0.0 for k in BANDS}
        assert bass_to_treble_ratio(bands) == pytest.approx(0.0)

    def test_bass_heavy(self):
        bands = {k: 0.0 for k in BANDS}
        bands["bass"] = 4.0
        bands["treble"] = 0.0
        assert bass_to_treble_ratio(bands) == pytest.approx(4.0)

    def test_treble_heavy(self):
        bands = {k: 0.0 for k in BANDS}
        bands["bass"] = 0.0
        bands["treble"] = 3.0
        assert bass_to_treble_ratio(bands) == pytest.approx(-3.0)


# ---------------------------------------------------------------------------
# extract_features
# ---------------------------------------------------------------------------

class TestExtractFeatures:
    def test_returns_all_expected_keys(self):
        freq, db = flat_curve()
        feats = extract_features(freq, db)
        expected = set(FEATURE_ORDER)
        assert expected.issubset(set(feats.keys()))

    def test_values_are_floats(self):
        freq, db = flat_curve(2.0)
        feats = extract_features(freq, db)
        for k, v in feats.items():
            assert isinstance(v, float), f"{k} should be float, got {type(v)}"

    def test_neutral_curve_near_zero(self):
        freq, db = flat_curve(0.0)
        feats = extract_features(freq, db)
        for k in ["sub_bass", "bass", "mids", "presence", "treble", "air"]:
            assert abs(feats[k]) < 0.5, f"{k} unexpectedly non-zero: {feats[k]}"


# ---------------------------------------------------------------------------
# to_vector
# ---------------------------------------------------------------------------

class TestToVector:
    def test_output_shape(self):
        freq, db = flat_curve()
        feats = extract_features(freq, db)
        vec = to_vector(feats)
        assert vec.shape == (len(FEATURE_ORDER),)

    def test_output_dtype_is_float(self):
        freq, db = flat_curve()
        feats = extract_features(freq, db)
        vec = to_vector(feats)
        assert vec.dtype == float

    def test_consistent_order(self):
        """to_vector output order must match FEATURE_ORDER."""
        feats = {k: float(i) for i, k in enumerate(FEATURE_ORDER)}
        vec = to_vector(feats)
        for i, k in enumerate(FEATURE_ORDER):
            assert vec[i] == pytest.approx(float(i))

    def test_missing_key_raises(self):
        """If a feature key is missing, to_vector should reject the profile."""
        with pytest.raises(ValueError):
            to_vector({"sub_bass": 1.0})  # incomplete dict
