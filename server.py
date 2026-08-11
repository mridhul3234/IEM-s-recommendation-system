"""
server.py

FastAPI server that exposes /search and /iem/{name} endpoints to the frontend.
"""

import os
import logging

import numpy as np
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

import time
from collections import defaultdict
from fastapi import FastAPI, Query, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware

from describe import describe
from features import extract_features, to_vector
from normalize import deviation_from_target, load_fr_csv, standard_grid
from embed import embed_texts
from infer import infer_target_profile
from search import hybrid_search
from explain import get_top_contributors

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rate Limiting & Security Configuration
# ---------------------------------------------------------------------------
from config import settings, validate_config

_ALLOWED_ORIGINS = settings.allowed_origins
_RATE_LIMIT_SEARCH_PER_MIN = settings.rate_limit_search
_IP_SEARCH_TIMESTAMPS: dict[str, list[float]] = defaultdict(list)

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
from data_manager import data_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_config(settings)
    data_manager.load_local_data()
    yield

app = FastAPI(title="IEM Recommendation Engine API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.middleware("http")
async def security_and_rate_limit_middleware(request: Request, call_next):
    # 1. Rate limiting for /search route
    if request.url.path == "/search":
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        # Clean timestamps older than 60s
        _IP_SEARCH_TIMESTAMPS[client_ip] = [
            ts for ts in _IP_SEARCH_TIMESTAMPS[client_ip] if now - ts < 60
        ]
        if len(_IP_SEARCH_TIMESTAMPS[client_ip]) >= _RATE_LIMIT_SEARCH_PER_MIN:
            logger.warning("Rate limit exceeded for IP: %s", client_ip)
            return Response(
                content='{"detail":"Rate limit exceeded. Maximum 30 search requests per minute."}',
                status_code=429,
                media_type="application/json",
            )
        _IP_SEARCH_TIMESTAMPS[client_ip].append(now)

    # 2. Process request
    response: Response = await call_next(request)

    # 3. Inject Security Headers
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    return response


# ---------------------------------------------------------------------------
# Global Exception Handler (Sanitized 500 Responses)
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server exception on %s: %s", request.url.path, exc)
    return Response(
        content='{"error":"Internal Server Error","detail":"An unexpected server error occurred."}',
        status_code=500,
        media_type="application/json",
    )


# ---------------------------------------------------------------------------
# Health & Uptime Endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
@app.get("/api/health")
def health_check():
    from db import is_supabase_configured
    return {
        "status": "ok",
        "service": "AcousticSearch API",
        "supabase_configured": is_supabase_configured(),
        "local_items_loaded": len(data_manager.iems) if data_manager.iems else 0,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


# ---------------------------------------------------------------------------
# /search
# ---------------------------------------------------------------------------

@app.get("/search")
def search_api(
    response: Response,
    q: str = Query(""),
    alpha: float = Query(0.5, ge=0.0, le=1.0),
    top_k: int = Query(6, ge=1, le=50),
    price_tier: str = Query("all"),
    exact_features: str = Query(None),
):
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=120"
    import json

    if exact_features:
        try:
            inferred_features = json.loads(exact_features)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid exact_features JSON: {exc}") from exc
        # Pure acoustic mode when there is no text query
        if not q.strip():
            alpha = 1.0
    else:
        inferred_features = infer_target_profile(q)

    inferred_vector = to_vector(inferred_features)

    from search_repository import fetch_search_candidates, filter_by_price_tier

    search_iems_data, search_descriptions, search_corpus_vectors, search_corpus_embeddings = (
        fetch_search_candidates(q)
    )

    search_iems_data, search_descriptions, search_corpus_vectors, search_corpus_embeddings = (
        filter_by_price_tier(
            search_iems_data, search_descriptions,
            search_corpus_vectors, search_corpus_embeddings,
            price_tier,
        )
    )

    results = hybrid_search(
        query=q,
        inferred_profile=inferred_vector,
        corpus_texts=search_descriptions,
        corpus_embeddings=search_corpus_embeddings,
        corpus_vectors=search_corpus_vectors,
        alpha=alpha,
        top_k=top_k,
    )

    output = []
    for _rank, (idx, score, sem_score, ac_score, desc) in enumerate(results, 1):
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
            "target_features": inferred_features,
        })

    return {"results": output, "inferred_features": inferred_features}


# ---------------------------------------------------------------------------
# /iem/{name}
# ---------------------------------------------------------------------------

@app.get("/iem/{name}")
def get_iem_api(name: str, response: Response):
    response.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=600"
    from db import is_supabase_configured

    if not is_supabase_configured():
        return _get_iem_local(name)

    try:
        from db import get_client, search_iems
        client = get_client()

        res = client.table("iems").select("*").eq("name", name).execute()
        if not res.data:
            return {"error": "IEM not found"}

        iem_data = res.data[0]

        embedding = iem_data.get("embedding")
        similar_items = []
        if embedding:
            db_results = search_iems(client, np.array(embedding), top_k=6)
            for sr in db_results:
                if sr["name"] != name:
                    similar_items.append({
                        "name": sr["name"],
                        "description": sr["description"],
                        "features": sr["features"],
                    })
                    if len(similar_items) == 5:
                        break

        return {"iem": iem_data, "similar": similar_items}

    except Exception as exc:
        logger.exception("Error fetching IEM from Supabase: %s", name)
        return {"error": str(exc)}


def _get_iem_local(name: str) -> dict:
    """Local-dataset fallback for /iem/{name}."""
    iem_idx = next(
        (i for i, (n, _f) in enumerate(data_manager.iems) if n == name),
        None,
    )
    if iem_idx is None:
        return {"error": "IEM not found"}

    iem_name, iem_feats = data_manager.iems[iem_idx]
    iem_desc = data_manager.descriptions[iem_idx]

    query_emb = data_manager.corpus_embeddings[iem_idx]
    norms = (
        np.linalg.norm(data_manager.corpus_embeddings, axis=1)
        * np.linalg.norm(query_emb)
    )
    norms[norms == 0] = 1  # avoid division by zero
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
            "features": sim_feats,
        })
        if len(similar_items) == 5:
            break

    return {
        "iem": {"name": iem_name, "description": iem_desc, "features": iem_feats},
        "similar": similar_items,
    }


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host=os.environ.get("BACKEND_HOST", "0.0.0.0"),
        port=int(os.environ.get("BACKEND_PORT", 8000)),
        reload=True,
    )
