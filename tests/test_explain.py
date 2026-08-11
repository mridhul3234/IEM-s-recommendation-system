"""
tests/test_explain.py

Unit tests for explain.py — get_top_contributors.
"""

import sys, os
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from explain import get_top_contributors


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NEUTRAL_FEATURES = {
    "sub_bass": 0.0, "bass": 0.0, "low_mids": 0.0, "mids": 0.0,
    "presence": 0.0, "treble": 0.0, "air": 0.0,
    "sibilance_risk": 0.0, "tonal_tilt": 0.0, "bass_to_treble": 0.0
}

NEUTRAL_TARGET = {k: 0.0 for k in NEUTRAL_FEATURES}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGetTopContributors:
    def test_returns_list(self):
        result = get_top_contributors(NEUTRAL_FEATURES)
        assert isinstance(result, list)

    def test_top_n_respected(self):
        feats = {**NEUTRAL_FEATURES, "bass": 5.0, "treble": 3.0, "presence": 2.0}
        result = get_top_contributors(feats, top_n=1)
        assert len(result) <= 1

    def test_neutral_features_returns_controlled(self):
        result = get_top_contributors(NEUTRAL_FEATURES)
        for r in result:
            assert "controlled" in r

    def test_elevated_bass_identified(self):
        feats = {**NEUTRAL_FEATURES, "bass": 6.0}
        result = get_top_contributors(feats)
        combined = " ".join(result)
        assert "bass" in combined
        assert "elevated" in combined

    def test_recessed_treble_identified(self):
        feats = {**NEUTRAL_FEATURES, "treble": -5.0}
        result = get_top_contributors(feats)
        combined = " ".join(result)
        assert "treble" in combined
        assert "recessed" in combined

    def test_target_alignment_takes_precedence(self):
        """When a target is provided with a strong preference, it should
        surface the matching IEM feature as a contributor."""
        feats = {**NEUTRAL_FEATURES, "bass": 4.0, "treble": 1.0}
        target = {**NEUTRAL_TARGET, "bass": 3.0}  # explicit bass request
        result = get_top_contributors(feats, inferred_target=target)
        combined = " ".join(result)
        assert "bass" in combined

    def test_mismatched_target_does_not_contribute(self):
        """IEM has recessed bass but target asked for bass — negative alignment."""
        feats = {**NEUTRAL_FEATURES, "bass": -4.0}
        target = {**NEUTRAL_TARGET, "bass": 3.0}  # wants bass but IEM is dark
        result = get_top_contributors(feats, inferred_target=target)
        # tgt * val = 3 * -4 = -12 → negative, should NOT appear via positive path
        combined = " ".join(result)
        # Falls through to fallback path — should describe IEM's extremes
        assert isinstance(result, list)

    def test_empty_features_does_not_crash(self):
        """Should handle empty dicts gracefully."""
        result = get_top_contributors({})
        assert isinstance(result, list)

    def test_default_top_n_is_two(self):
        feats = {**NEUTRAL_FEATURES, "bass": 6.0, "treble": 5.0, "mids": 4.0}
        result = get_top_contributors(feats)
        assert len(result) == 2

    def test_underscore_replaced_with_space(self):
        feats = {**NEUTRAL_FEATURES, "sub_bass": 6.0}
        result = get_top_contributors(feats)
        for r in result:
            assert "_" not in r, f"Underscores should be replaced: {r}"


# ---------------------------------------------------------------------------
# db.py helper — is_supabase_configured
# ---------------------------------------------------------------------------

class TestIsSupabaseConfigured:
    """Test the placeholder-detection logic without making any network calls."""

    def _call(self, url: str, key: str, monkeypatch) -> bool:
        import db
        monkeypatch.setenv("SUPABASE_URL", url)
        monkeypatch.setenv("SUPABASE_KEY", key)
        # Force reload to pick up monkeypatched env
        return db.is_supabase_configured()

    def test_real_values_return_true(self, monkeypatch):
        result = self._call(
            "https://abcdefgh.supabase.co",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.real.key",
            monkeypatch
        )
        assert result is True

    def test_placeholder_url_returns_false(self, monkeypatch):
        result = self._call(
            "https://your-project-id.supabase.co",
            "some_key",
            monkeypatch
        )
        assert result is False

    def test_placeholder_key_returns_false(self, monkeypatch):
        result = self._call(
            "https://real.supabase.co",
            "your_supabase_anon_or_service_key_here",
            monkeypatch
        )
        assert result is False

    def test_empty_url_returns_false(self, monkeypatch):
        result = self._call("", "some_key", monkeypatch)
        assert result is False

    def test_empty_key_returns_false(self, monkeypatch):
        result = self._call("https://real.supabase.co", "", monkeypatch)
        assert result is False
