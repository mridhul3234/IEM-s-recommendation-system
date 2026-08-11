"""
server.py

FastAPI server that exposes a `/search` endpoint to the frontend.
"""

import glob
import os
import sys
import numpy as np
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from describe import describe
from features import extract_features, to_vector
from normalize import deviation_from_target, load_fr_csv, standard_grid
from embed import embed_texts
from infer import infer_target_profile
from search import hybrid_search
from explain import get_top_contributors

app = FastAPI(title="IEM Recommendation Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For local dev
    allow_methods=["*"],
    allow_headers=["*"],
)

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET_PATH = os.path.join(HERE, "sample_data", "targets", "Harman in-ear 2019.csv")
IEM_DIR = os.path.join(HERE, "sample_data", "in-ear")

from data_manager import data_manager

@app.on_event("startup")
def startup_event():
    data_manager.load_local_data()

@app.get("/search")
def search_api(q: str = Query(""), alpha: float = Query(0.5), top_k: int = Query(6), price_tier: str = Query("all"), exact_features: str = Query(None)):
    import json
    # If exact_features are provided, parse them and skip LLM.
    if exact_features:
        inferred_features = json.loads(exact_features)
        # Force alpha to 1.0 (pure acoustic math) if there is no text query
        if not q.strip():
            alpha = 1.0
    else:
        inferred_features = infer_target_profile(q)
        
    inferred_vector = to_vector(inferred_features)
    
    from search_repository import fetch_search_candidates, filter_by_price_tier
    
    # 1. Fetch Candidates (Supabase or Local)
    search_iems_data, search_descriptions, search_corpus_vectors, search_corpus_embeddings = fetch_search_candidates(q)
    
    # 2. Apply Filters (Price Tier)
    search_iems_data, search_descriptions, search_corpus_vectors, search_corpus_embeddings = filter_by_price_tier(
        search_iems_data, search_descriptions, search_corpus_vectors, search_corpus_embeddings, price_tier
    )

    results = hybrid_search(
        query=q,
        inferred_profile=inferred_vector,
        corpus_texts=search_descriptions,
        corpus_embeddings=search_corpus_embeddings,
        corpus_vectors=search_corpus_vectors,
        alpha=alpha,
        top_k=top_k
    )
    
    output = []
    for rank, (idx, score, sem_score, ac_score, desc) in enumerate(results, 1):
        iem_name = search_iems_data[idx][0]
        iem_features = search_iems_data[idx][1]
        contributors = get_top_contributors(iem_features, inferred_features)
        
        output.append({
            "name": iem_name,
            "description": desc,
            "score": round(score, 3),
            "semantic_score": round(sem_score, 3),
            "acoustic_score": round(ac_score, 3),
            "contributors": contributors,
            "features": iem_features,
            "target_features": inferred_features
        })
        
    return {"results": output, "inferred_features": inferred_features}

@app.get("/iem/{name}")
def get_iem_api(name: str):
    from db import is_supabase_configured
    use_supabase = is_supabase_configured()
    if not use_supabase:
        from data_manager import data_manager
        import numpy as np
        
        iem_idx = next((i for i, (n, f) in enumerate(data_manager.iems) if n == name), None)
        if iem_idx is None:
            return {"error": "IEM not found"}
            
        iem_name, iem_feats = data_manager.iems[iem_idx]
        iem_desc = data_manager.descriptions[iem_idx]
        
        query_emb = data_manager.corpus_embeddings[iem_idx]
        norms = np.linalg.norm(data_manager.corpus_embeddings, axis=1) * np.linalg.norm(query_emb)
        norms[norms == 0] = 1 # avoid division by zero
        similarities = np.dot(data_manager.corpus_embeddings, query_emb) / norms
        
        top_indices = np.argsort(similarities)[::-1]
        
        similar_items = []
        for idx in top_indices:
            if idx == iem_idx:
                continue
            sim_name, sim_feats = data_manager.iems[idx]
            similar_items.append({
                "name": sim_name,
                "description": data_manager.descriptions[idx],
                "features": sim_feats
            })
            if len(similar_items) == 5:
                break
                
        return {
            "iem": {
                "name": iem_name,
                "description": iem_desc,
                "features": iem_feats
            },
            "similar": similar_items
        }
        
    try:
        from db import get_client, search_iems
        client = get_client()
        
        # 1. Fetch the exact IEM
        res = client.table("iems").select("*").eq("name", name).execute()
        if not res.data:
            return {"error": "IEM not found"}
            
        iem_data = res.data[0]
        
        # 2. Fetch similar IEMs using its embedding
        embedding = iem_data.get('embedding')
        similar_items = []
        if embedding:
            # search_iems returns list of dicts. We request top_k=6 because the 1st match will be the IEM itself
            import numpy as np
            db_results = search_iems(client, np.array(embedding), top_k=6)
            for sr in db_results:
                if sr['name'] != name:
                    similar_items.append({
                        "name": sr['name'],
                        "description": sr['description'],
                        "features": sr['features']
                    })
                    if len(similar_items) == 5:
                        break
                        
        return {
            "iem": iem_data,
            "similar": similar_items
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
