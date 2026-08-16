"""Repository behavior when the configured data source is unavailable."""

import pytest


def test_configured_repository_failure_does_not_fall_back_to_local(monkeypatch):
    from acousticsearch import db, search_repository

    monkeypatch.setattr(db, "is_supabase_configured", lambda: True)
    monkeypatch.setattr(db, "get_client", lambda: (_ for _ in ()).throw(RuntimeError("offline")))

    with pytest.raises(search_repository.SearchRepositoryUnavailable):
        search_repository.fetch_search_candidates("warm bass")
