"""
search_repository.py

Encapsulates data fetching from Supabase and business-logic filters.
"""

import logging
import numpy as np

from .embed import embed_texts
from .features import to_vector
from .data_manager import data_manager

logger = logging.getLogger(__name__)

# Price threshold (USD) separating "cheaper" from "costlier" tiers.
PRICE_TIER_THRESHOLD = 500
SEMANTIC_CANDIDATE_POOL_MIN = 100
SEMANTIC_CANDIDATE_POOL_MAX = 1_000


def _semantic_candidate_pool_size(semantic_weight: float) -> int:
    """Widen semantic pre-filtering as the final rank becomes acoustic-heavy."""
    weight = min(1.0, max(0.0, float(semantic_weight)))
    return max(
        SEMANTIC_CANDIDATE_POOL_MIN,
        int(SEMANTIC_CANDIDATE_POOL_MAX * (1.0 - weight)),
    )


class SearchRepositoryUnavailable(RuntimeError):
    """The configured production repository could not serve a search."""


def _records_to_candidates(records: list[dict]) -> tuple[list, list, np.ndarray, np.ndarray]:
    """Convert complete, valid database records into ranking inputs."""
    from .db import parse_embedding

    iems_data: list[tuple[str, dict]] = []
    descriptions: list[str] = []
    vectors: list[np.ndarray] = []
    parsed_embeddings: list[np.ndarray | None] = []

    for record in records:
        try:
            features = record["features"]
            vectors.append(to_vector(features))
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning("Skipping invalid Supabase IEM record %r: %s", record.get("name"), exc)
            continue

        iems_data.append((record["name"], features))
        descriptions.append(str(record.get("description") or ""))
        parsed_embeddings.append(parse_embedding(record.get("embedding")))

    if not iems_data:
        return [], [], np.empty((0, 10)), np.empty((0, 384))

    if all(emb is not None for emb in parsed_embeddings):
        corpus_embeddings = np.asarray(parsed_embeddings, dtype=float)
    else:
        corpus_embeddings = embed_texts(descriptions)

    return iems_data, descriptions, np.asarray(vectors), np.asarray(corpus_embeddings)



def fetch_search_candidates(q: str, semantic_weight: float = 0.5):
    """
    Fetch the initial candidate set for hybrid ranking.

    Uses Supabase semantic pre-filtering only when semantic relevance has a
    non-zero weight. Pure acoustic search reads all measured records, so a
    textually dissimilar but acoustically correct match cannot be discarded.

    Returns:
        tuple: (iems_data, descriptions, corpus_vectors, corpus_embeddings)
    """
    from .db import is_supabase_configured
    if is_supabase_configured():
        if not (q.strip() or semantic_weight == 0.0):
            return [], [], np.empty((0, 10)), np.empty((0, 384))
        try:
            from .db import get_client, list_iems, search_iems
            client = get_client()
            if semantic_weight == 0.0:
                db_results = list_iems(client)
            else:
                query_emb = embed_texts([q])[0]
                db_results = search_iems(
                    client,
                    query_emb,
                    top_k=_semantic_candidate_pool_size(semantic_weight),
                )

            if db_results:
                candidates = _records_to_candidates(db_results)
                if candidates[0]:
                    return candidates
                raise SearchRepositoryUnavailable("Supabase returned no valid measured records.")
            return [], [], np.empty((0, 10)), np.empty((0, 384))
        except Exception as exc:
            if isinstance(exc, SearchRepositoryUnavailable):
                raise
            logger.exception("Supabase query failed.")
            raise SearchRepositoryUnavailable("Supabase search is unavailable.") from exc

    if not data_manager.iems or data_manager.corpus_vectors is None or data_manager.corpus_embeddings is None:
        raise SearchRepositoryUnavailable("Local measured corpus is unavailable.")
    return (
        data_manager.iems,
        data_manager.descriptions,
        data_manager.corpus_vectors,
        data_manager.corpus_embeddings,
    )


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
            price = float(feats["price"]) if isinstance(feats, dict) else None
        except (ValueError, TypeError):
            price = None

        # An absent price is not evidence that an IEM is cheap. It is excluded
        # from a tiered result rather than silently bucketed below $500.
        if price_tier == "cheaper" and price is not None and price < PRICE_TIER_THRESHOLD:
            filtered_iems.append((name, feats))
            filtered_descs.append(descriptions[i])
            filtered_vecs.append(vectors[i])
            filtered_indices.append(i)
        elif price_tier == "costlier" and price is not None and price >= PRICE_TIER_THRESHOLD:
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

    # Empty is an honest result: returning an unfiltered collection would make
    # the active price tier lie to the user.
    vector_width = vectors.shape[1] if vectors.ndim == 2 else 10
    embedding_width = embeddings.shape[1] if embeddings.ndim == 2 else 384
    return [], [], np.empty((0, vector_width)), np.empty((0, embedding_width))
