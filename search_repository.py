"""
search_repository.py

Encapsulates data fetching from Supabase and applying business logic filters.
"""
import os
import numpy as np
from embed import embed_texts
from features import to_vector
from data_manager import data_manager

def fetch_search_candidates(q: str):
    """
    Fetches the initial K candidates for hybrid ranking.
    Uses Supabase if available and if a semantic text query exists.
    Otherwise, falls back to the full local dataset.
    """
    search_iems_data = data_manager.iems
    search_descriptions = data_manager.descriptions
    search_corpus_vectors = data_manager.corpus_vectors
    search_corpus_embeddings = data_manager.corpus_embeddings
    
    from db import is_supabase_configured
    use_supabase = is_supabase_configured()
    
    if use_supabase and q.strip():
        try:
            from db import get_client, search_iems
            client = get_client()
            query_emb = embed_texts([q])[0]
            db_results = search_iems(client, query_emb, top_k=20)
            
            if db_results:
                db_iems_data = []
                db_descriptions = []
                corpus_vectors_list = []
                for res in db_results:
                    db_iems_data.append((res['name'], res['features']))
                    db_descriptions.append(res['description'])
                    corpus_vectors_list.append(to_vector(res['features']))
                
                search_iems_data = db_iems_data
                search_descriptions = db_descriptions
                search_corpus_vectors = np.array(corpus_vectors_list)
                search_corpus_embeddings = embed_texts(search_descriptions)
            else:
                print("Supabase returned 0 items. Falling back to local dataset.")
        except Exception as e:
            print(f"Supabase query failed, using local fallback. Error: {e}")
            
    return search_iems_data, search_descriptions, search_corpus_vectors, search_corpus_embeddings

def filter_by_price_tier(iems_data, descriptions, vectors, embeddings, price_tier: str):
    """
    Filters the candidate arrays by price tier.
    """
    if price_tier not in ("cheaper", "costlier"):
        return iems_data, descriptions, vectors, embeddings

    filtered_iems = []
    filtered_descs = []
    filtered_vecs = []
    
    for i, (name, feats) in enumerate(iems_data):
        try:
            price = float(feats.get("price", 0)) if isinstance(feats, dict) else 0
        except (ValueError, TypeError):
            price = 0
            
        if price_tier == "cheaper" and price < 500:
            filtered_iems.append((name, feats))
            filtered_descs.append(descriptions[i])
            filtered_vecs.append(vectors[i])
        elif price_tier == "costlier" and price >= 500:
            filtered_iems.append((name, feats))
            filtered_descs.append(descriptions[i])
            filtered_vecs.append(vectors[i])
            
    if filtered_iems:
        return filtered_iems, filtered_descs, np.array(filtered_vecs), embed_texts(filtered_descs)
    
    return iems_data, descriptions, vectors, embeddings
