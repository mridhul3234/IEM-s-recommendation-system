"""
search.py

Performs semantic search to find the closest matching texts for a given query.
"""

from __future__ import annotations

import numpy as np
from embed import embed_texts

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Compute cosine similarity between vector a and matrix b."""
    a_norm = np.linalg.norm(a)
    b_norm = np.linalg.norm(b, axis=1)
    # Avoid division by zero
    if a_norm == 0:
        return np.zeros(len(b))
    return np.dot(b, a) / (a_norm * b_norm)

def semantic_search(query: str, corpus_texts: list[str], corpus_embeddings: np.ndarray, top_k: int = 3):
    """
    Embed the query and find the top-k most similar texts in the corpus.
    Returns a list of tuples: (index, score, text).
    """
    query_emb = embed_texts([query])[0]
    
    similarities = cosine_similarity(query_emb, corpus_embeddings)
    
    # Get top-k indices
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    results = []
    for idx in top_indices:
        results.append((int(idx), float(similarities[idx]), corpus_texts[idx]))
        
    return results
