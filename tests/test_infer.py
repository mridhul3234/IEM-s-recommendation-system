"""
tests/test_infer.py

Unit tests for infer.py — parse_acoustic_json and infer_target_profile.
We mock all external API calls to keep tests hermetic.
"""

import json
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from infer import parse_acoustic_json

EXPECTED_KEYS = {
    "sub_bass", "bass", "low_mids", "mids", "presence",
    "treble", "air", "sibilance_risk", "tonal_tilt", "bass_to_treble"
}

DEFAULT_PROFILE = {k: 0.0 for k in EXPECTED_KEYS}


# ---------------------------------------------------------------------------
# parse_acoustic_json
# ---------------------------------------------------------------------------

class TestParseAcousticJson:
    def test_valid_json_returns_dict(self):
        payload = json.dumps({k: 1.5 for k in EXPECTED_KEYS})
        result = parse_acoustic_json(payload)
        assert isinstance(result, dict)

    def test_all_expected_keys_present(self):
        payload = json.dumps({k: 0.0 for k in EXPECTED_KEYS})
        result = parse_acoustic_json(payload)
        assert set(result.keys()) >= EXPECTED_KEYS

    def test_invalid_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            parse_acoustic_json("{bad json}")

    def test_empty_string_raises(self):
        with pytest.raises(json.JSONDecodeError):
            parse_acoustic_json("")

    def test_nested_json_doesnt_crash(self):
        payload = json.dumps({"sub_bass": 2.0, "extra": {"nested": True}})
        result = parse_acoustic_json(payload)
        assert result["sub_bass"] == 2.0


# ---------------------------------------------------------------------------
# infer_target_profile — with mocked API
# ---------------------------------------------------------------------------

class TestInferTargetProfile:
    def _good_response(self):
        return json.dumps({k: 1.0 for k in EXPECTED_KEYS})

    def test_falls_back_to_default_when_no_key(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "")
        # Patch Ollama to also fail
        monkeypatch.setattr("infer.call_ollama_fallback", lambda p: (_ for _ in ()).throw(Exception("no ollama")))
        from infer import infer_target_profile
        result = infer_target_profile("warm bass IEM")
        assert result == DEFAULT_PROFILE

    def test_returns_dict_with_placeholder_key(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "your_gemini_api_key_here")
        monkeypatch.setattr("infer.call_ollama_fallback", lambda p: (_ for _ in ()).throw(Exception("no ollama")))
        from infer import infer_target_profile
        result = infer_target_profile("test")
        assert isinstance(result, dict)
        assert set(result.keys()) == EXPECTED_KEYS

    def test_gemini_success_path(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyFakeButFormatCorrect12345678")
        monkeypatch.setattr("infer.call_gemini_api", lambda prompt, key: self._good_response())
        from infer import infer_target_profile
        result = infer_target_profile("warm")
        for k in EXPECTED_KEYS:
            assert k in result

    def test_gemini_failure_falls_to_ollama(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyFakeButFormatCorrect12345678")
        monkeypatch.setattr("infer.call_gemini_api", lambda p, k: (_ for _ in ()).throw(Exception("API fail")))
        monkeypatch.setattr("infer.call_ollama_fallback", lambda p: self._good_response())
        from infer import infer_target_profile
        result = infer_target_profile("test query")
        assert result["bass"] == 1.0

    def test_both_fail_returns_default(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyFakeButFormatCorrect12345678")
        monkeypatch.setattr("infer.call_gemini_api", lambda p, k: (_ for _ in ()).throw(Exception("fail")))
        monkeypatch.setattr("infer.call_ollama_fallback", lambda p: (_ for _ in ()).throw(Exception("fail")))
        from infer import infer_target_profile
        result = infer_target_profile("test")
        assert result == DEFAULT_PROFILE

    def test_empty_query_handled(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "")
        monkeypatch.setattr("infer.call_ollama_fallback", lambda p: (_ for _ in ()).throw(Exception("fail")))
        from infer import infer_target_profile
        result = infer_target_profile("")
        assert isinstance(result, dict)
