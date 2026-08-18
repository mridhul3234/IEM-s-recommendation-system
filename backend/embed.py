"""Bounded, process-safe Gemini embedding cache.

Embeddings are generated remotely to keep the deployed backend small: the
previous sentence-transformers/PyTorch stack exceeds lightweight host limits.
The configured vector column must use the same model and dimension as this
module; run ``migrate_to_supabase.py`` after changing either value.
"""

from __future__ import annotations

from collections import OrderedDict
from contextlib import contextmanager
import json
import logging
import os
import hashlib
from pathlib import Path
import tempfile
import threading
import time

import numpy as np

logger = logging.getLogger(__name__)

HERE = Path(__file__).resolve().parent
CACHE_FILE = HERE / "embeddings_cache.json"
LOCK_FILE = HERE / "embeddings_cache.lock"
MODEL_NAME = "gemini-embedding-001"
EMBEDDING_DIMENSION = 384
MAX_CACHE_ENTRIES = 2_000
REMOTE_EMBED_RETRIES = 3

_cache: OrderedDict[str, list[float]] | None = None
_cache_lock = threading.RLock()


@contextmanager
def _file_lock():
    """Lock cache writes across worker processes; atomic replacement protects readers."""
    LOCK_FILE.touch(exist_ok=True)
    with LOCK_FILE.open("a+") as lock_handle:
        if os.name == "nt":
            import msvcrt
            lock_handle.seek(0)
            lock_handle.write("0")
            lock_handle.flush()
            msvcrt.locking(lock_handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if os.name == "nt":
                lock_handle.seek(0)
                msvcrt.locking(lock_handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)


def _read_cache() -> OrderedDict[str, list[float]]:
    if not CACHE_FILE.exists():
        return OrderedDict()
    try:
        with CACHE_FILE.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
        if not isinstance(raw, dict):
            raise ValueError("cache root is not an object")
        cache = OrderedDict()
        for text, vector in raw.items():
            if isinstance(text, str) and isinstance(vector, list) and len(vector) == EMBEDDING_DIMENSION:
                cache[text] = vector
        return cache
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        logger.warning("Ignoring unreadable embedding cache: %s", exc)
        return OrderedDict()


def load_cache() -> OrderedDict[str, list[float]]:
    global _cache
    with _cache_lock:
        if _cache is None:
            _cache = _read_cache()
        return _cache


def _write_cache(cache: OrderedDict[str, list[float]]) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=CACHE_FILE.parent, delete=False) as handle:
        json.dump(cache, handle, separators=(",", ":"))
        temp_name = handle.name
    os.replace(temp_name, CACHE_FILE)


def _merge_and_save(new_entries: dict[str, list[float]]) -> None:
    global _cache
    with _cache_lock, _file_lock():
        disk_cache = _read_cache()
        disk_cache.update(new_entries)
        while len(disk_cache) > MAX_CACHE_ENTRIES:
            disk_cache.popitem(last=False)
        _write_cache(disk_cache)
        _cache = disk_cache


def _embed_remote(texts: list[str]) -> list[list[float]]:
    from google import genai
    from google.genai import types
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key or api_key.lower().startswith(("your_", "placeholder_")):
        raise RuntimeError("GEMINI_API_KEY is required to generate embeddings.")
    client = genai.Client(api_key=api_key)
    for attempt in range(REMOTE_EMBED_RETRIES):
        try:
            response = client.models.embed_content(
                model=MODEL_NAME,
                contents=texts,
                config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIMENSION),
            )
            break
        except Exception as exc:
            if attempt == REMOTE_EMBED_RETRIES - 1:
                raise
            delay = 0.25 * (2 ** attempt)
            logger.warning(
                "Gemini embedding attempt %d/%d failed; retrying in %.2fs: %s",
                attempt + 1, REMOTE_EMBED_RETRIES, delay, exc,
            )
            time.sleep(delay)
    vectors = [list(embedding.values) for embedding in response.embeddings]
    if len(vectors) != len(texts) or any(len(vector) != EMBEDDING_DIMENSION for vector in vectors):
        raise RuntimeError("Gemini returned embeddings with an unexpected shape.")
    return vectors


def _offline_embeddings(texts: list[str]) -> np.ndarray:
    """Stable local retrieval fallback for development without a model download."""
    matrix = np.zeros((len(texts), EMBEDDING_DIMENSION), dtype=float)
    for row, text in enumerate(texts):
        for token in text.casefold().split():
            index = int.from_bytes(hashlib.blake2b(token.encode("utf-8"), digest_size=4).digest(), "big") % EMBEDDING_DIMENSION
            matrix[row, index] += 1.0
        norm = np.linalg.norm(matrix[row])
        if norm:
            matrix[row] /= norm
    return matrix


def embed_texts(texts: list[str]) -> np.ndarray:
    """Return embeddings with a bounded cache and atomic, locked persistence."""
    if not texts:
        return np.empty((0, EMBEDDING_DIMENSION), dtype=float)

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key or api_key.lower().startswith(("your_", "placeholder_")):
        logger.warning("Using deterministic local embeddings because Gemini is not configured.")
        return _offline_embeddings(texts)

    cache = load_cache()
    result: list[list[float] | None] = [None] * len(texts)
    missing: list[str] = []
    missing_indices: list[int] = []
    with _cache_lock:
        for index, text in enumerate(texts):
            cached = cache.get(text)
            if cached is not None:
                cache.move_to_end(text)
                result[index] = cached
            else:
                missing.append(text)
                missing_indices.append(index)

    if missing:
        try:
            new_vectors = _embed_remote(missing)
        except Exception as exc:
            # Keep ranking available during a transient remote outage. Do not
            # persist fallback vectors; a later healthy request can refresh them.
            logger.warning("Gemini embeddings unavailable; using local fallback: %s", exc)
            new_vectors = _offline_embeddings(missing).tolist()
            new_entries = {}
        else:
            new_entries = dict(zip(missing, new_vectors))
        for index, vector in zip(missing_indices, new_vectors):
            result[index] = vector
        if new_entries:
            _merge_and_save(new_entries)

    return np.asarray(result, dtype=float)
