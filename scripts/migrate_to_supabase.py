"""
migrate_to_supabase.py

Reads all local IEM CSV files, processes features and embeddings, 
and pushes them to Supabase via db.py.
"""

import glob
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import settings
from backend.db import get_client, upsert_iem
from backend.describe import describe
from backend.embed import embed_texts
from backend.features import extract_features
from backend.normalize import deviation_from_target, load_fr_csv, standard_grid

TARGET_PATH = PROJECT_ROOT / "data" / "sample_data" / "targets" / "Harman in-ear 2019.csv"
IEM_DIR = PROJECT_ROOT / "data" / "sample_data" / "in-ear"

def load_verified_prices(path: str | None) -> dict[str, dict]:
    """Load only explicitly reviewed price entries with an exact product name."""
    if not path:
        return {}
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Price catalog must be a JSON array.")
    prices: dict[str, dict] = {}
    for entry in payload:
        if not isinstance(entry, dict) or entry.get("review_status") != "approved":
            continue
        name = entry.get("name")
        try:
            price = float(entry["price"])
        except (KeyError, TypeError, ValueError):
            continue
        if not isinstance(name, str) or not name.strip() or price < 0:
            continue
        if not entry.get("source_url") or not entry.get("verified_at"):
            continue
        prices[name] = {"price": price, "price_currency": entry.get("currency", "USD"),
                        "price_source_url": entry["source_url"], "price_verified_at": entry["verified_at"]}
    return prices

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if settings.is_production and "--confirm-production" not in sys.argv:
        print("⚠️ WARNING: You are attempting to run migrations against a PRODUCTION environment!")
        print("To proceed, re-run with the flag: python migrate_to_supabase.py --confirm-production")
        sys.exit(1)

    price_catalog_path = None
    if "--price-catalog" in sys.argv:
        try:
            price_catalog_path = sys.argv[sys.argv.index("--price-catalog") + 1]
        except IndexError:
            print("Error: --price-catalog requires a JSON file path.")
            sys.exit(1)
    try:
        verified_prices = load_verified_prices(price_catalog_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error loading verified price catalog: {exc}")
        sys.exit(1)

    try:
        client = get_client()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
        
    print("✅ Connected to Supabase")
    
    target = load_fr_csv(TARGET_PATH, name="Harman in-ear 2019")
    grid = standard_grid()
    
    iem_paths = sorted(glob.glob(str(IEM_DIR / "*.csv")))
    if not iem_paths:
        print("No IEM data found in sample_data/in-ear/")
        sys.exit(1)

    print(f"✅ Found {len(iem_paths)} IEMs locally")

    descriptions = []
    metadata = []

    for path in iem_paths:
        iem = load_fr_csv(path)
        freq, deviation = deviation_from_target(iem, target, grid_hz=grid)
        feats = extract_features(freq, deviation)
        iem_name_clean = os.path.basename(path).replace(".csv", "")
        feats["acoustic_profile_source"] = "local_measurement"
        feats["embedding_model"] = "gemini-embedding-001:384"
        if price := verified_prices.get(iem_name_clean):
            feats.update(price)
        desc = describe(feats, iem_name=iem_name_clean)
        
        metadata.append({
            "name": iem.name,
            "features": feats,
            "description": desc
        })
        descriptions.append(desc)

    print(f"✅ Extracted features and generated descriptions")

    # Embed corpus
    corpus_embeddings = embed_texts(descriptions)
    print(f"✅ Embedded corpus descriptions")

    # Upsert to Supabase
    for i, meta in enumerate(metadata):
        print(f"Uploading {meta['name']}...")
        upsert_iem(
            client=client,
            name=meta['name'],
            description=meta['description'],
            features=meta['features'],
            embedding=corpus_embeddings[i]
        )
        
    print("✅ Migration to Supabase complete!")

if __name__ == "__main__":
    main()
