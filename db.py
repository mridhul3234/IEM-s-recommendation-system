"""
db.py

Handles connections and operations with the Supabase pgvector backend.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
import numpy as np

load_dotenv()

def get_client() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables must be set.")
    return create_client(url, key)

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
