"""
server.py

FastAPI server that exposes a `/search` endpoint to the frontend.
"""

import glob
import os
import sys
import numpy as np

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

# Keep everything loaded in memory for the fallback path
target = None
grid = None
iems = []
descriptions = []
corpus_vectors = None
corpus_embeddings = None

@app.on_event("startup")
def startup_event():
    global target, grid, iems, descriptions, corpus_vectors, corpus_embeddings
    print("Loading local fallback data...")
    target = load_fr_csv(TARGET_PATH, name="Harman in-ear 2019")
    grid = standard_grid()
    
    iem_paths = sorted(glob.glob(os.path.join(IEM_DIR, "*.csv")))
    
    corpus_vectors_list = []
    
    for path in iem_paths:
        iem = load_fr_csv(path)
        freq, deviation = deviation_from_target(iem, target, grid_hz=grid)
        feats = extract_features(freq, deviation)
        iem_name_clean = os.path.basename(path).replace(".csv", "")
        desc = describe(feats, iem_name=iem_name_clean)
        
        # Inject deterministic mock price for testing
        mock_price = (sum(ord(c) for c in iem_name_clean) % 500) + 49
        feats["price"] = mock_price

        
        iems.append((iem_name_clean, feats))
        descriptions.append(desc)
        corpus_vectors_list.append(to_vector(feats))

        # Create some artificial variations so the dataset is larger than 8 items!
        variants = [
            (" Pro", 1.2, 80),
            (" MkII", 0.9, -30)
        ]
        
        for suffix, feat_mult, price_adj in variants:
            var_name = iem_name_clean + suffix
            var_feats = {k: v * feat_mult if isinstance(v, (int, float)) else v for k, v in feats.items()}
            var_feats["price"] = max(20, mock_price + price_adj)
            var_desc = desc + f" This is the {suffix.strip()} variant, offering a slightly altered signature."
            iems.append((var_name, var_feats))
            descriptions.append(var_desc)
            corpus_vectors_list.append(to_vector(var_feats))

    corpus_vectors = np.array(corpus_vectors_list)
    corpus_embeddings = embed_texts(descriptions)
    print("Local fallback data loaded.")

@app.get("/search")
def search_api(q: str = Query(...), alpha: float = Query(0.5), top_k: int = Query(6), price_tier: str = Query("all")):
    # Infer features
    inferred_features = infer_target_profile(q)
    inferred_vector = to_vector(inferred_features)
    
    # Try Supabase first
    use_supabase = os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_KEY")
    
    # Setup variables for search
    search_iems_data = iems
    search_descriptions = descriptions
    search_corpus_vectors = corpus_vectors
    search_corpus_embeddings = corpus_embeddings
    
    if use_supabase:
        try:
            from db import get_client, search_iems
            client = get_client()
            query_emb = embed_texts([q])[0]
            db_results = search_iems(client, query_emb, top_k=20)
            
            if db_results:
                # Reconstruct for hybrid search
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
    
    # Apply Price Tier Filtering if requested ("cheaper" = < 500, "costlier" = >= 500)
    if price_tier in ("cheaper", "costlier"):
        filtered_iems = []
        filtered_descs = []
        filtered_vecs = []
        
        for i, (name, feats) in enumerate(search_iems_data):
            try:
                price = float(feats.get("price", 0)) if isinstance(feats, dict) else 0
            except (ValueError, TypeError):
                price = 0
                
            if price_tier == "cheaper" and price < 500:
                filtered_iems.append((name, feats))
                filtered_descs.append(search_descriptions[i])
                filtered_vecs.append(search_corpus_vectors[i])
            elif price_tier == "costlier" and price >= 500:
                filtered_iems.append((name, feats))
                filtered_descs.append(search_descriptions[i])
                filtered_vecs.append(search_corpus_vectors[i])
                
        if filtered_iems:
            search_iems_data = filtered_iems
            search_descriptions = filtered_descs
            search_corpus_vectors = np.array(filtered_vecs)
            search_corpus_embeddings = embed_texts(search_descriptions)

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
    use_supabase = os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_KEY")
    if not use_supabase:
        return {"error": "Supabase not configured"}
        
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
