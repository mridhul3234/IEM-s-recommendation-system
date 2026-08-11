"""
search_repository.py

Encapsulates data fetching from Supabase and business-logic filters.
"""

import logging
import numpy as np

from embed import embed_texts
from features import to_vector
from data_manager import data_manager

logger = logging.getLogger(__name__)

# Price threshold (USD) separating "cheaper" from "costlier" tiers.
PRICE_TIER_THRESHOLD = 500


def fetch_search_candidates(q: str):
    """
    Fetch the initial candidate set for hybrid ranking.

    Uses Supabase for semantic pre-filtering when it is configured and a
    text query is present; otherwise falls back to the full local dataset.

    Returns:
        tuple: (iems_data, descriptions, corpus_vectors, corpus_embeddings)
    """
    search_iems_data = data_manager.iems
    search_descriptions = data_manager.descriptions
    search_corpus_vectors = data_manager.corpus_vectors
    search_corpus_embeddings = data_manager.corpus_embeddings

    from db import is_supabase_configured
    if is_supabase_configured() and q.strip():
        try:
            from db import get_client, search_iems
            client = get_client()
            query_emb = embed_texts([q])[0]
            db_results = search_iems(client, query_emb, top_k=20)

            if db_results:
                db_iems_data = [(r["name"], r["features"]) for r in db_results]
                db_descriptions = [r["description"] for r in db_results]
                corpus_vectors_list = [to_vector(r["features"]) for r in db_results]

                search_iems_data = db_iems_data
                search_descriptions = db_descriptions
                search_corpus_vectors = np.array(corpus_vectors_list)
                search_corpus_embeddings = embed_texts(search_descriptions)
            else:
                logger.warning("Supabase returned 0 results; falling back to local dataset.")
        except Exception as exc:
            logger.warning("Supabase query failed, using local fallback: %s", exc)

    return search_iems_data, search_descriptions, search_corpus_vectors, search_corpus_embeddings


def filter_by_price_tier(
    iems_data: list,
    descriptions: list,
    vectors: np.ndarray,
    embeddings: np.ndarray,
    price_tier: str,
) -> tuple:
    """
    Filter candidate arrays by price tier.

    Args:
        price_tier: "cheaper" (<$500), "costlier" (≥$500), or any other
                    value to skip filtering.

    Returns the same 4-tuple, filtered in-place (or unchanged if the
    filtered set would be empty).
    """
    if price_tier not in ("cheaper", "costlier"):
        return iems_data, descriptions, vectors, embeddings

    filtered_iems: list = []
    filtered_descs: list = []
    filtered_vecs: list = []

    filtered_indices: list[int] = []

    for i, (name, feats) in enumerate(iems_data):
        try:
            price = float(feats.get("price", 0)) if isinstance(feats, dict) else 0.0
        except (ValueError, TypeError):
            price = 0.0

        if price_tier == "cheaper" and price < PRICE_TIER_THRESHOLD:
            filtered_iems.append((name, feats))
            filtered_descs.append(descriptions[i])
            filtered_vecs.append(vectors[i])
            filtered_indices.append(i)
        elif price_tier == "costlier" and price >= PRICE_TIER_THRESHOLD:
            filtered_iems.append((name, feats))
            filtered_descs.append(descriptions[i])
            filtered_vecs.append(vectors[i])
            filtered_indices.append(i)

    if filtered_iems:
        filtered_embeddings = (
            embeddings[filtered_indices]
            if embeddings is not None and len(embeddings) == len(iems_data)
            else embed_texts(filtered_descs)
        )
        return (
            filtered_iems,
            filtered_descs,
            np.array(filtered_vecs),
            filtered_embeddings,
        )

    # Filtering resulted in empty set — return unfiltered to avoid blank results.
    logger.warning("Price-tier filter '%s' matched 0 items; returning unfiltered set.", price_tier)
    return iems_data, descriptions, vectors, embeddings
