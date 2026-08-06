"""
query_cli.py

CLI entry point for Phase A.
Runs the full pipeline: loads sample data -> normalize -> features -> 
describe -> embed -> search.

Usage:
    python query_cli.py "warm bass, no sibilance, good for vocals"
"""

import argparse
import glob
import os
import sys

from describe import describe
from features import extract_features
from normalize import deviation_from_target, load_fr_csv, standard_grid
from embed import embed_texts
from search import semantic_search

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET_PATH = os.path.join(HERE, "sample_data", "targets", "Harman in-ear 2019.csv")
IEM_DIR = os.path.join(HERE, "sample_data", "in-ear")

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description="IEM Recommendation Engine - Semantic Search MVP")
    parser.add_argument("query", type=str, help="Free-text query for the tonal description you want")
    parser.add_argument("--top_k", type=int, default=3, help="Number of results to return")
    args = parser.parse_args()

    print(f"✅ [Parsed query: '{args.query}']")

    target = load_fr_csv(TARGET_PATH, name="Harman in-ear 2019")
    grid = standard_grid()
    
    iem_paths = sorted(glob.glob(os.path.join(IEM_DIR, "*.csv")))
    if not iem_paths:
        print("No IEM data found in sample_data/in-ear/")
        sys.exit(1)

    print(f"✅ [Loaded {len(iem_paths)} IEMs and target curve]")

    iems = []
    descriptions = []

    for path in iem_paths:
        iem = load_fr_csv(path)
        freq, deviation = deviation_from_target(iem, target, grid_hz=grid)
        feats = extract_features(freq, deviation)
        iem_name_clean = os.path.basename(path).replace(".csv", "")
        desc = describe(feats, iem_name=iem_name_clean)
        
        iems.append((iem.name, feats))
        descriptions.append(desc)

    print(f"✅ [Extracted features and generated descriptions for corpus]")

    # Embed corpus
    corpus_embeddings = embed_texts(descriptions)
    print(f"✅ [Embedded corpus descriptions]")

    # Search
    results = semantic_search(args.query, descriptions, corpus_embeddings, top_k=args.top_k)
    print(f"✅ [Computed similarity scores]")
    print("\n--- Search Results ---")
    for rank, (idx, score, desc) in enumerate(results, 1):
        iem_name = os.path.basename(iems[idx][0]).replace(".csv", "")
        print(f"{rank}. {iem_name} (Score: {score:.3f})")
        print(f"   {desc}")
        print()

if __name__ == "__main__":
    main()
