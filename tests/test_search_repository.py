"""Repository behavior when the configured data source is unavailable."""

import pytest
import numpy as np


def test_configured_repository_failure_does_not_fall_back_to_local(monkeypatch):
    from backend import db, search_repository

    monkeypatch.setattr(db, "is_supabase_configured", lambda: True)
    monkeypatch.setattr(db, "get_client", lambda: (_ for _ in ()).throw(RuntimeError("offline")))

    with pytest.raises(search_repository.SearchRepositoryUnavailable):
        search_repository.fetch_search_candidates("warm bass")


def _record(name: str = "Measured IEM") -> dict:
    return {
        "name": name,
        "description": "Text unrelated to the requested tuning.",
        "features": {
            "sub_bass": 0.0, "bass": 0.0, "low_mids": 0.0, "mids": 0.0,
            "presence": 0.0, "treble": 0.0, "air": 0.0,
            "sibilance_risk": 0.0, "tonal_tilt": 0.0, "bass_to_treble": 0.0,
        },
        "embedding": [0.0] * 384,
    }


def test_acoustic_heavy_search_widens_supabase_semantic_pool(monkeypatch):
    """Do not discard acoustic matches in the old fixed top-100 shortlist."""
    from backend import db, search_repository

    observed = {}
    monkeypatch.setattr(db, "is_supabase_configured", lambda: True)
    monkeypatch.setattr(db, "get_client", lambda: object())
    monkeypatch.setattr(search_repository, "embed_texts", lambda _texts: np.zeros((1, 384)))
    monkeypatch.setattr(
        db,
        "search_iems",
        lambda _client, _embedding, top_k: observed.setdefault("top_k", top_k) and [_record()],
    )

    candidates = search_repository.fetch_search_candidates("warm bass", semantic_weight=0.05)

    assert candidates[0][0][0] == "Measured IEM"
    assert observed["top_k"] == 950


def test_pure_acoustic_search_reads_all_records(monkeypatch):
    from backend import db, search_repository

    monkeypatch.setattr(db, "is_supabase_configured", lambda: True)
    monkeypatch.setattr(db, "get_client", lambda: object())
    monkeypatch.setattr(db, "list_iems", lambda _client: [_record()])
    monkeypatch.setattr(db, "search_iems", lambda *_args, **_kwargs: pytest.fail("semantic RPC should not run"))

    candidates = search_repository.fetch_search_candidates("", semantic_weight=0.0)

    assert candidates[0][0][0] == "Measured IEM"


def test_list_iems_fetches_every_page():
    from backend.db import list_iems

    class Response:
        def __init__(self, data):
            self.data = data

    class Query:
        def __init__(self):
            self.start = 0

        def select(self, _fields):
            return self

        def range(self, start, _end):
            self.start = start
            return self

        def execute(self):
            pages = {
                0: [{"name": "A"}, {"name": "B"}],
                2: [{"name": "C"}],
            }
            return Response(pages[self.start])

    class Client:
        def table(self, _name):
            return Query()

    assert [record["name"] for record in list_iems(Client(), page_size=2)] == ["A", "B", "C"]


def test_parse_embedding():
    import json
    from backend.db import parse_embedding

    # Valid float list
    arr = parse_embedding([0.1, 0.2, 0.3])
    assert arr is not None and np.allclose(arr, [0.1, 0.2, 0.3])

    # Valid string-serialized JSON vector
    arr_str = parse_embedding(json.dumps([0.5, 0.6, 0.7]))
    assert arr_str is not None and np.allclose(arr_str, [0.5, 0.6, 0.7])

    # Missing / None
    assert parse_embedding(None) is None

    # Malformed string
    assert parse_embedding("invalid json") is None

    # Empty array
    assert parse_embedding([]) is None


def test_records_to_candidates_handles_string_and_missing_embeddings(monkeypatch):
    import json
    from backend import search_repository

    monkeypatch.setattr(search_repository, "embed_texts", lambda descs: np.ones((len(descs), 384)))

    rec_string = _record("String IEM")
    rec_string["embedding"] = json.dumps([0.1] * 384)

    rec_missing = _record("RPC IEM")
    del rec_missing["embedding"]

    iems, descs, vecs, embs = search_repository._records_to_candidates([rec_string, rec_missing])

    assert len(iems) == 2
    assert iems[0][0] == "String IEM"
    assert iems[1][0] == "RPC IEM"
    assert embs.shape == (2, 384)

