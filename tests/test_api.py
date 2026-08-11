"""
tests/test_api.py

Integration tests for the FastAPI endpoints via the HTTPX TestClient.
All external services (Gemini, Supabase, embed model) are monkeypatched
so tests run without network or GPU.
"""

import json
import numpy as np
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MOCK_FEATURES = {
    "sub_bass": 2.0, "bass": 4.0, "low_mids": 0.5, "mids": -0.5,
    "presence": 1.0, "treble": -1.0, "air": 0.0,
    "sibilance_risk": 1.5, "tonal_tilt": -0.3, "bass_to_treble": 5.0,
    "price": 249
}

MOCK_IEM_DATA = [
    ("7Hz Timeless",   {**MOCK_FEATURES, "price": 219}),
    ("Moondrop Aria",  {**MOCK_FEATURES, "price": 79}),
    ("Thieaudio Monarch MkII", {**MOCK_FEATURES, "price": 899}),
]

MOCK_DESCRIPTIONS = [
    "A warm, bass-forward IEM with excellent detail.",
    "A neutral-bright signature with excellent clarity.",
    "A reference-class hybrid with extended treble.",
]


@pytest.fixture(autouse=True)
def patch_data_manager(monkeypatch):
    """Make data_manager return a small in-memory dataset."""
    import data_manager as dm
    mock_vecs = np.random.rand(len(MOCK_IEM_DATA), 10)
    mock_embs = np.random.rand(len(MOCK_IEM_DATA), 384)
    monkeypatch.setattr(dm.data_manager, "iems", MOCK_IEM_DATA)
    monkeypatch.setattr(dm.data_manager, "descriptions", MOCK_DESCRIPTIONS)
    monkeypatch.setattr(dm.data_manager, "corpus_vectors", mock_vecs)
    monkeypatch.setattr(dm.data_manager, "corpus_embeddings", mock_embs)


@pytest.fixture(autouse=True)
def patch_embed(monkeypatch):
    """Replace embed_texts with a fast random embedding."""
    import embed
    monkeypatch.setattr(embed, "embed_texts", lambda texts: np.random.rand(len(texts), 384))


@pytest.fixture(autouse=True)
def patch_infer(monkeypatch):
    """Replace infer_target_profile with a neutral profile."""
    import infer
    neutral = {
        "sub_bass": 0.0, "bass": 0.0, "low_mids": 0.0, "mids": 0.0,
        "presence": 0.0, "treble": 0.0, "air": 0.0,
        "sibilance_risk": 0.0, "tonal_tilt": 0.0, "bass_to_treble": 0.0
    }
    monkeypatch.setattr(infer, "infer_target_profile", lambda q: neutral)


@pytest.fixture(autouse=True)
def patch_supabase(monkeypatch):
    """Always report Supabase as NOT configured → use local fallback."""
    import db
    monkeypatch.setattr(db, "is_supabase_configured", lambda: False)


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    import importlib
    import server as srv
    importlib.reload(srv)
    return TestClient(srv.app)


# ---------------------------------------------------------------------------
# GET /search
# ---------------------------------------------------------------------------

class TestSearchEndpoint:
    def test_basic_search_returns_200(self, client):
        res = client.get("/search?q=warm+bass")
        assert res.status_code == 200

    def test_response_has_results_key(self, client):
        res = client.get("/search?q=test")
        data = res.json()
        assert "results" in data

    def test_response_has_inferred_features(self, client):
        res = client.get("/search?q=test")
        data = res.json()
        assert "inferred_features" in data

    def test_empty_query_returns_results(self, client):
        """Empty query should still return results (EQ mode fallback)."""
        res = client.get("/search?q=")
        assert res.status_code == 200

    def test_top_k_is_respected(self, client):
        res = client.get("/search?q=test&top_k=1")
        data = res.json()
        assert len(data["results"]) <= 1

    def test_result_item_has_expected_fields(self, client):
        res = client.get("/search?q=bass")
        data = res.json()
        if data["results"]:
            item = data["results"][0]
            for field in ["name", "description", "score", "contributors", "features"]:
                assert field in item, f"Missing field: {field}"

    def test_price_tier_all_returns_results(self, client):
        res = client.get("/search?q=test&price_tier=all")
        assert res.status_code == 200

    def test_price_tier_cheaper_filters(self, client):
        res = client.get("/search?q=test&price_tier=cheaper")
        data = res.json()
        for item in data["results"]:
            price = item["features"].get("price", 0)
            assert price < 500, f"Expected price < 500, got {price}"

    def test_exact_features_mode(self, client):
        feats = json.dumps({
            "sub_bass": 2.0, "bass": 3.0, "low_mids": 0.0, "mids": 0.0,
            "presence": 0.0, "treble": 0.0, "air": 0.0,
            "sibilance_risk": 0.0, "tonal_tilt": 0.0, "bass_to_treble": 0.0
        })
        res = client.get(f"/search?q=&exact_features={feats}")
        assert res.status_code == 200
        data = res.json()
        assert "results" in data

    def test_malformed_exact_features_raises_error(self, client):
        res = client.get("/search?q=&exact_features={bad_json}")
        # Server should return 500 or a JSON error — not crash silently
        assert res.status_code in (400, 422, 500)


# ---------------------------------------------------------------------------
# GET /iem/{name}
# ---------------------------------------------------------------------------

class TestIemEndpoint:
    def test_known_iem_returns_data(self, client):
        res = client.get("/iem/7Hz%20Timeless")
        assert res.status_code == 200
        data = res.json()
        assert "iem" in data
        assert data["iem"]["name"] == "7Hz Timeless"

    def test_known_iem_has_similar_key(self, client):
        res = client.get("/iem/7Hz%20Timeless")
        data = res.json()
        assert "similar" in data

    def test_unknown_iem_returns_error(self, client):
        res = client.get("/iem/NonExistentIEM9999")
        assert res.status_code == 200
        data = res.json()
        assert "error" in data

    def test_url_encoded_name(self, client):
        res = client.get("/iem/Moondrop%20Aria")
        assert res.status_code == 200

    def test_similar_items_are_list(self, client):
        res = client.get("/iem/7Hz%20Timeless")
        data = res.json()
        assert isinstance(data.get("similar"), list)
