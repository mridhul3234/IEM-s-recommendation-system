"""
embed.py

Handles generating embeddings from text descriptions using sentence-transformers.
Includes an on-disk cache to avoid re-embedding unchanged descriptions.
"""

from __future__ import annotations

import json
import os
import numpy as np

# sentence_transformers is imported lazily to keep CLI startup fast
# if embeddings are fully cached

CACHE_FILE = "embeddings_cache.json"
MODEL_NAME = "all-MiniLM-L6-v2"

_model = None

def get_model():
    global _model
    if _model is None:
        # Prevent huggingface from trying to check for updates and hanging on HTTP 429s
        os.environ["HF_HUB_OFFLINE"] = "1"
        from sentence_transformers import SentenceTransformer
        try:
            _model = SentenceTransformer(MODEL_NAME, local_files_only=True)
        except Exception:
            # Fallback if not fully cached, though it usually is
            os.environ["HF_HUB_OFFLINE"] = "0"
            _model = SentenceTransformer(MODEL_NAME)
    return _model

_cache: dict[str, list[float]] | None = None

def load_cache() -> dict[str, list[float]]:
    global _cache
    if _cache is None:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as f:
                _cache = json.load(f)
        else:
            _cache = {}
    return _cache

def save_cache(cache: dict[str, list[float]]):
    global _cache
    _cache = cache
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, separators=(',', ':'))

def embed_texts(texts: list[str]) -> np.ndarray:
    """
    Embed a list of text strings, returning a numpy array of shape (N, dim).
    Uses a local JSON cache keyed by the exact text string.
    """
    cache = load_cache()
    embeddings = []
    
    texts_to_embed = []
    indices_to_embed = []
    
    for i, text in enumerate(texts):
        if text in cache:
            embeddings.append(cache[text])
        else:
            embeddings.append(None) # placeholder
            texts_to_embed.append(text)
            indices_to_embed.append(i)
            
    if texts_to_embed:
        model = get_model()
        new_embs = model.encode(texts_to_embed, convert_to_numpy=True)
        
        for i, idx in enumerate(indices_to_embed):
            emb_list = new_embs[i].tolist()
            embeddings[idx] = emb_list
            cache[texts_to_embed[i]] = emb_list
            
        save_cache(cache)
        
    return np.array(embeddings, dtype=float)
