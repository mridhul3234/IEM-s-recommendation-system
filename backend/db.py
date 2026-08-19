"""
db.py

Handles connections and operations with the Supabase pgvector backend.
"""

import json
from typing import Any
from functools import lru_cache

from supabase import create_client, Client
import numpy as np
from .config import settings

def parse_embedding(emb_val: Any) -> np.ndarray | None:
    """Parse an embedding value into a 1D float numpy array.

    Handles lists, tuples, numpy arrays, and JSON strings (such as pgvector output from Supabase).
    Returns None if the value cannot be parsed into a finite 1D array.
    """
    if emb_val is None:
        return None
    if isinstance(emb_val, str):
        try:
            emb_val = json.loads(emb_val)
        except (json.JSONDecodeError, TypeError):
            return None
    if isinstance(emb_val, (list, tuple, np.ndarray)):
        try:
            arr = np.asarray(emb_val, dtype=float)
            if arr.ndim == 1 and len(arr) > 0 and np.all(np.isfinite(arr)):
                return arr
        except (ValueError, TypeError):
            return None
    return None


def is_supabase_configured() -> bool:
    return settings.is_supabase_configured

@lru_cache(maxsize=1)
def get_client() -> Client:
    """Return the process-wide Supabase client and reuse its HTTP transport."""
    if not is_supabase_configured():
        raise ValueError("SUPABASE_URL and SUPABASE_KEY are not validly configured in .env.")
    return create_client(settings.supabase_url, settings.supabase_key)

def upsert_iem(client: Client, name: str, description: str, features: dict, embedding: np.ndarray):
    """Inserts or updates an IEM in the Supabase database."""
    # Convert numpy array to list for JSON serialization
    emb_list = embedding.tolist()
    
    data = {
        "name": name,
        "description": description,
        "features": features,
        "embedding": emb_list
    }
    
    # We use upsert on the 'name' column which is unique
    response = client.table("iems").upsert(data, on_conflict="name").execute()
    return response

def search_iems(client: Client, query_embedding: np.ndarray, top_k: int = 10) -> list[dict]:
    """
    Searches for the closest IEMs by semantic similarity using the match_iems RPC.
    """
    emb_list = query_embedding.tolist()
    
    response = client.rpc(
        "match_iems", 
        {"query_embedding": emb_list, "match_count": top_k}
    ).execute()
    
    return response.data


def list_iems(client: Client, page_size: int = 1000) -> list[dict]:
    """Fetch all measured IEMs for pure acoustic ranking, with pagination."""
    records: list[dict] = []
    start = 0
    while True:
        response = (
            client.table("iems").select("name,description,features,embedding")
            .range(start, start + page_size - 1).execute()
        )
        batch = response.data or []
        records.extend(batch)
        if len(batch) < page_size:
            return records
        start += page_size
