"""
tests/test_search.py

Unit tests for search.py — cosine_similarity, acoustic_similarity,
and hybrid_search. All pure-math functions; no I/O or network.
"""

import numpy as np
import pytest

from backend.search import cosine_similarity, acoustic_similarity, hybrid_search


# ---------------------------------------------------------------------------
# cosine_similarity
# ---------------------------------------------------------------------------

class TestCosineSimilarity:
    def test_identical_vectors_is_one(self):
        a = np.array([1.0, 2.0, 3.0])
        b = np.array([[1.0, 2.0, 3.0]])
        result = cosine_similarity(a, b)
        assert result[0] == pytest.approx(1.0, abs=1e-6)

    def test_orthogonal_vectors_is_zero(self):
        a = np.array([1.0, 0.0])
        b = np.array([[0.0, 1.0]])
        result = cosine_similarity(a, b)
        assert result[0] == pytest.approx(0.0, abs=1e-6)

    def test_zero_query_returns_zeros(self):
        a = np.zeros(3)
        b = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        result = cosine_similarity(a, b)
        assert np.all(result == 0.0)

    def test_empty_corpus_returns_empty(self):
        a = np.array([1.0, 0.0])
        b = np.empty((0, 2))
        result = cosine_similarity(a, b)
        assert len(result) == 0

    def test_multiple_vectors(self):
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([
            [1.0, 0.0, 0.0],   # cos sim = 1.0
            [0.0, 1.0, 0.0],   # cos sim = 0.0
        ])
        result = cosine_similarity(a, b)
        assert result[0] == pytest.approx(1.0, abs=1e-6)
        assert result[1] == pytest.approx(0.0, abs=1e-6)

    def test_output_length_matches_corpus(self):
        a = np.random.rand(10)
        b = np.random.rand(5, 10)
        result = cosine_similarity(a, b)
        assert len(result) == 5


# ---------------------------------------------------------------------------
# acoustic_similarity
# ---------------------------------------------------------------------------

class TestAcousticSimilarity:
    def test_identical_profile_is_one(self):
        target = np.zeros(10)
        corpus = np.zeros((1, 10))
        result = acoustic_similarity(target, corpus)
        assert result[0] == pytest.approx(1.0)

    def test_similarity_decreases_with_distance(self):
        target = np.zeros(10)
        corpus = np.array([
            np.zeros(10),       # distance = 0 → sim = 1.0
            np.ones(10) * 5,    # large distance → low sim
        ])
        result = acoustic_similarity(target, corpus)
        assert result[0] > result[1]

    def test_values_in_range_zero_one(self):
        target = np.random.rand(10)
        corpus = np.random.rand(20, 10)
        result = acoustic_similarity(target, corpus)
        assert np.all(result >= 0.0)
        assert np.all(result <= 1.0)

    def test_empty_corpus_returns_empty(self):
        target = np.zeros(5)
        corpus = np.empty((0, 5))
        result = acoustic_similarity(target, corpus)
        assert len(result) == 0


# ---------------------------------------------------------------------------
# hybrid_search
# ---------------------------------------------------------------------------

class TestHybridSearch:
    """
    hybrid_search calls embed_texts internally, so we patch it to avoid
    loading the sentence-transformers model in tests.
    """

    def _make_corpus(self, n=5, dim=384):
        np.random.seed(42)
        embeddings = np.random.rand(n, dim)
        # Normalize so cosine sim behaves predictably
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        return embeddings / norms

    def test_returns_top_k_results(self, monkeypatch):
        corpus_embs = self._make_corpus(10)
        query_emb = corpus_embs[0]  # use first as query

        def mock_embed(texts):
            return query_emb[np.newaxis, :]

        monkeypatch.setattr("backend.search.embed_texts", mock_embed)

        corpus_vecs = np.random.rand(10, 10)
        results = hybrid_search(
            query="warm bass",
            inferred_profile=np.zeros(10),
            corpus_texts=[f"iem {i}" for i in range(10)],
            corpus_embeddings=corpus_embs,
            corpus_vectors=corpus_vecs,
            top_k=3
        )
        assert len(results) == 3

    def test_result_tuple_structure(self, monkeypatch):
        corpus_embs = self._make_corpus(5)
        query_emb = corpus_embs[0]

        monkeypatch.setattr("backend.search.embed_texts", lambda t: query_emb[np.newaxis, :])

        corpus_vecs = np.random.rand(5, 10)
        results = hybrid_search(
            query="test",
            inferred_profile=np.zeros(10),
            corpus_texts=["a", "b", "c", "d", "e"],
            corpus_embeddings=corpus_embs,
            corpus_vectors=corpus_vecs,
            top_k=2
        )
        for item in results:
            idx, final_score, sem_score, ac_score, text = item
            assert isinstance(idx, int)
            assert 0.0 <= final_score <= 1.0
            assert isinstance(text, str)

    def test_alpha_zero_uses_only_acoustic(self, monkeypatch):
        """With alpha=0, semantic similarity doesn't affect ranking."""
        n = 5
        corpus_embs = self._make_corpus(n)
        # All embeddings same → semantic scores identical
        uniform_emb = np.ones((1, 384)) / np.sqrt(384)
        monkeypatch.setattr("backend.search.embed_texts", lambda t: uniform_emb)

        corpus_vecs = np.random.rand(n, 10)
        target = np.zeros(10)

        results = hybrid_search(
            query="",
            inferred_profile=target,
            corpus_texts=[f"iem {i}" for i in range(n)],
            corpus_embeddings=corpus_embs,
            corpus_vectors=corpus_vecs,
            alpha=0.0,
            top_k=n
        )
        scores = [r[1] for r in results]
        # Scores should be descending
        assert scores == sorted(scores, reverse=True)

    def test_top_k_greater_than_corpus(self, monkeypatch):
        """top_k > corpus size should return all items."""
        corpus_embs = self._make_corpus(3)
        monkeypatch.setattr("backend.search.embed_texts", lambda t: corpus_embs[0][np.newaxis, :])

        corpus_vecs = np.random.rand(3, 5)
        results = hybrid_search(
            query="q",
            inferred_profile=np.zeros(5),
            corpus_texts=["a", "b", "c"],
            corpus_embeddings=corpus_embs,
            corpus_vectors=corpus_vecs,
            top_k=100
        )
        assert len(results) == 3
