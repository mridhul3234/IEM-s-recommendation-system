"""
migrate_to_supabase.py

Reads all local IEM CSV files, processes features and embeddings, 
and pushes them to Supabase via db.py.
"""

import glob
import os
import sys

from describe import describe
from features import extract_features
from normalize import deviation_from_target, load_fr_csv, standard_grid
from embed import embed_texts
from db import get_client, upsert_iem

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET_PATH = os.path.join(HERE, "sample_data", "targets", "Harman in-ear 2019.csv")
IEM_DIR = os.path.join(HERE, "sample_data", "in-ear")

def main():
    try:
        client = get_client()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
        
    print("✅ Connected to Supabase")
    
    target = load_fr_csv(TARGET_PATH, name="Harman in-ear 2019")
    grid = standard_grid()
    
    iem_paths = sorted(glob.glob(os.path.join(IEM_DIR, "*.csv")))
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
