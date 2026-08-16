"""
search.py

Performs semantic search to find the closest matching texts for a given query.
"""

from __future__ import annotations

import numpy as np
from .embed import embed_texts

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Compute cosine similarity between vector a and matrix b."""
    if len(b) == 0:
        return np.array([])
    a_norm = np.linalg.norm(a)
    b_norm = np.linalg.norm(b, axis=1) if b.ndim > 1 else np.linalg.norm(b)
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

def acoustic_similarity(inferred_vector: np.ndarray, corpus_vectors: np.ndarray) -> np.ndarray:
    """Compute an acoustic similarity score in [0, 1] using Euclidean distance."""
    if len(corpus_vectors) == 0:
        return np.array([])
    # Distance shape: (N,)
    distances = np.linalg.norm(corpus_vectors - inferred_vector, axis=1) if corpus_vectors.ndim > 1 else np.linalg.norm(corpus_vectors - inferred_vector)
    # Convert distance to similarity
    return 1.0 / (1.0 + distances)

def hybrid_search(query: str, inferred_profile: np.ndarray, corpus_texts: list[str], 
                  corpus_embeddings: np.ndarray, corpus_vectors: np.ndarray, 
                  alpha: float = 0.5, top_k: int = 3):
    """
    Perform a hybrid search using both semantic text similarity and acoustic feature similarity.
    alpha: Weight for semantic similarity. (1 - alpha) is for acoustic similarity.
    Returns: list of tuples (index, final_score, semantic_score, acoustic_score, text)
    """
    ac_sims = acoustic_similarity(inferred_profile, corpus_vectors)
    if alpha == 0.0:
        sem_sims = np.zeros(len(corpus_texts))
    else:
        query_emb = embed_texts([query])[0]
        sem_sims = cosine_similarity(query_emb, corpus_embeddings)
    
    # Normalize semantic similarities which can be in [-1, 1] loosely to [0, 1]
    # Though MiniLM embeddings usually yield cosine sim in [0, 1] for most text.
    sem_sims_norm = np.clip(sem_sims, 0, 1)
    
    final_scores = alpha * sem_sims_norm + (1.0 - alpha) * ac_sims
    
    top_indices = np.argsort(final_scores)[::-1][:top_k]
    
    results = []
    for idx in top_indices:
        results.append((
            int(idx), 
            float(final_scores[idx]), 
            float(sem_sims[idx]), 
            float(ac_sims[idx]), 
            corpus_texts[idx]
        ))
        
    return results
