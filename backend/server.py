"""
server.py

FastAPI server that exposes /search and /iem/{name} endpoints to the frontend.
"""

import logging

import numpy as np
from contextlib import asynccontextmanager
import time
from collections import OrderedDict, deque
from threading import Lock
from fastapi import FastAPI, Query, HTTPException, Response, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .features import to_vector
from .infer import infer_target_profile
from .search import hybrid_search
from .explain import get_top_contributors

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rate Limiting & Security Configuration
# ---------------------------------------------------------------------------
from .config import settings, validate_config

_ALLOWED_ORIGINS = settings.allowed_origins
_RATE_LIMIT_SEARCH_PER_MIN = settings.rate_limit_search
_RATE_LIMIT_MAX_CLIENTS = settings.rate_limit_max_clients
_IP_SEARCH_TIMESTAMPS: OrderedDict[str, deque[float]] = OrderedDict()
_RATE_LIMIT_LOCK = Lock()

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
from .data_manager import data_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_config(settings)
    from .db import is_supabase_configured
    if is_supabase_configured():
        # Production must serve its measured database, not a partial local
        # corpus whose descriptions would trigger extra embedding work.
        data_manager.clear()
        logger.info("Supabase configured; local fallback corpus is disabled.")
    else:
        data_manager.load_local_data()
    yield

app = FastAPI(title="IEM Recommendation Engine API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def security_and_rate_limit_middleware(request: Request, call_next):
    if request.method != "OPTIONS" and request.url.path == "/search":
        origin = request.headers.get("origin")
        if origin:
            clean_origin = origin.rstrip("/")
            if clean_origin not in _ALLOWED_ORIGINS and "*" not in _ALLOWED_ORIGINS:
                logger.warning("CORS rejected origin '%s'. Configured ALLOWED_ORIGINS: %s", origin, _ALLOWED_ORIGINS)
                return Response(content='{"detail":"Origin is not allowed"}', status_code=403, media_type="application/json")

    # Bounded per-process rate limiting. Deploy an edge limiter too when
    # running multiple workers, because memory is not shared between them.
    if request.url.path == "/search":
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        with _RATE_LIMIT_LOCK:
            timestamps = _IP_SEARCH_TIMESTAMPS.get(client_ip, deque())
            while timestamps and now - timestamps[0] >= 60:
                timestamps.popleft()
            if len(timestamps) >= _RATE_LIMIT_SEARCH_PER_MIN:
                logger.warning("Rate limit exceeded for IP: %s", client_ip)
                return Response(
                    content=f'{{"detail":"Rate limit exceeded. Maximum {_RATE_LIMIT_SEARCH_PER_MIN} search requests per minute."}}',
                    status_code=429, media_type="application/json",
                )
            timestamps.append(now)
            _IP_SEARCH_TIMESTAMPS[client_ip] = timestamps
            _IP_SEARCH_TIMESTAMPS.move_to_end(client_ip)
            while len(_IP_SEARCH_TIMESTAMPS) > _RATE_LIMIT_MAX_CLIENTS:
                _IP_SEARCH_TIMESTAMPS.popitem(last=False)

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
    from .db import is_supabase_configured
    return {
        "status": "ok",
        "service": "AcousticSearch API",
        "supabase_configured": is_supabase_configured(),
        "local_items_loaded": len(data_manager.iems) if data_manager.iems else 0,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


@app.get("/ready")
def readiness_check():
    """Verify the active data source rather than only reporting its config."""
    from .db import get_client, is_supabase_configured

    if not is_supabase_configured():
        ready = bool(data_manager.iems and data_manager.corpus_vectors is not None)
        detail = "local corpus is loaded" if ready else "local corpus is unavailable"
    else:
        try:
            get_client().table("iems").select("name").limit(1).execute()
            ready, detail = True, "Supabase is reachable"
        except Exception as exc:
            logger.warning("Readiness check could not reach Supabase: %s", exc)
            ready, detail = False, "Supabase is unreachable"

    payload = {"status": "ready" if ready else "unavailable", "detail": detail}
    return payload if ready else JSONResponse(status_code=503, content=payload)


# ---------------------------------------------------------------------------
# /search
# ---------------------------------------------------------------------------

@app.get("/search")
def search_api(
    response: Response,
    q: str = Query("", max_length=500),
    alpha: float = Query(0.5, ge=0.0, le=1.0),
    top_k: int = Query(6, ge=1, le=50),
    price_tier: str = Query("all"),
    exact_features: str = Query(None, max_length=10_000),
):
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=120"
    import json

    if exact_features:
        try:
            inferred_features = json.loads(exact_features)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid exact_features JSON: {exc}") from exc
        # Pure acoustic mode when there is no text query.
        if not q.strip():
            alpha = 0.0
    else:
        inferred_features = infer_target_profile(q)

    try:
        inferred_vector = to_vector(inferred_features)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    from .search_repository import (
        SearchRepositoryUnavailable,
        fetch_search_candidates,
        filter_by_price_tier,
    )

    try:
        search_iems_data, search_descriptions, search_corpus_vectors, search_corpus_embeddings = (
            fetch_search_candidates(q, semantic_weight=alpha)
        )
    except SearchRepositoryUnavailable as exc:
        raise HTTPException(status_code=503, detail="Search data is temporarily unavailable") from exc

    search_iems_data, search_descriptions, search_corpus_vectors, search_corpus_embeddings = (
        filter_by_price_tier(
            search_iems_data, search_descriptions,
            search_corpus_vectors, search_corpus_embeddings,
            price_tier,
        )
    )

    if not search_iems_data:
        return {"results": [], "inferred_features": inferred_features}

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
    from .db import is_supabase_configured

    if not is_supabase_configured():
        return _get_iem_local(name)

    try:
        from .db import get_client, search_iems
        client = get_client()

        res = client.table("iems").select("*").eq("name", name).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="IEM not found")

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

    except HTTPException:
        raise
    except Exception:
        logger.exception("Error fetching IEM from Supabase: %s", name)
        raise HTTPException(status_code=503, detail="IEM data is temporarily unavailable")


def _get_iem_local(name: str) -> dict:
    """Local-dataset fallback for /iem/{name}."""
    if data_manager.corpus_embeddings is None:
        raise HTTPException(status_code=503, detail="Local measurement data is temporarily unavailable")
    iem_idx = next(
        (i for i, (n, _f) in enumerate(data_manager.iems) if n == name),
        None,
    )
    if iem_idx is None:
        raise HTTPException(status_code=404, detail="IEM not found")

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
