"""
db.py

Handles connections and operations with the Supabase pgvector backend.
"""

from supabase import create_client, Client
import numpy as np
from .config import settings

def is_supabase_configured() -> bool:
    return settings.is_supabase_configured

def get_client() -> Client:
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
