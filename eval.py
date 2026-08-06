"""
eval.py

Evaluation harness to test precision@k on known IEM archetypes.
"""

import glob
import os
import sys
import numpy as np

from describe import describe
from features import extract_features, to_vector
from normalize import deviation_from_target, load_fr_csv, standard_grid
from embed import embed_texts
from infer import infer_target_profile
from search import hybrid_search

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET_PATH = os.path.join(HERE, "sample_data", "targets", "Harman in-ear 2019.csv")
IEM_DIR = os.path.join(HERE, "sample_data", "in-ear")

ARCHETYPES = {
    "basshead or very warm": ["1MORE Triple Driver LTNG", "Campfire Audio Andromeda"],
    "perfectly neutral, balanced": ["Moondrop Blessing 2"],
    "bright, highly energetic, sibilant treble": ["7Hz Timeless", "AKG N5005", "Sennheiser IE 900"]
}

def main():
    target = load_fr_csv(TARGET_PATH, name="Harman in-ear 2019")
    grid = standard_grid()
    
    iem_paths = sorted(glob.glob(os.path.join(IEM_DIR, "*.csv")))
    
    iems = []
    descriptions = []
    corpus_vectors_list = []

    print("Loading corpus...")
    for path in iem_paths:
        iem = load_fr_csv(path)
        freq, deviation = deviation_from_target(iem, target, grid_hz=grid)
        feats = extract_features(freq, deviation)
        
        # Debug: Print feature tables for sibilant IEMs to calibrate sibilance_risk
        if iem.name in ["7Hz Timeless", "Sennheiser IE 900", "AKG N5005", "Moondrop Blessing 2", "1MORE Triple Driver LTNG", "Campfire Audio Andromeda"]:
            print(f"[{iem.name}] Sibilance Risk: {feats['sibilance_risk']}, Presence: {feats['presence']}, Treble: {feats['treble']}")
            
        iem_name_clean = os.path.basename(path).replace(".csv", "")
        desc = describe(feats, iem_name=iem_name_clean)
        
        iems.append((iem.name, feats))
        descriptions.append(desc)
        corpus_vectors_list.append(to_vector(feats))

    corpus_vectors = np.array(corpus_vectors_list)
    corpus_embeddings = embed_texts(descriptions)
    
    alphas = [1.0, 0.7, 0.5, 0.3, 0.0]
    top_k = 3
    
    print("\n--- Running Evaluations ---")
    for query, expected_iems in ARCHETYPES.items():
        print(f"\nQuery: '{query}'")
        print(f"Expected targets: {expected_iems}")
        
        inferred_features = infer_target_profile(query)
        inferred_vector = to_vector(inferred_features)
        print(f"Inferred target profile: {inferred_features}")
        
        for alpha in alphas:
            results = hybrid_search(
                query=query,
                inferred_profile=inferred_vector,
                corpus_texts=descriptions,
                corpus_embeddings=corpus_embeddings,
                corpus_vectors=corpus_vectors,
                alpha=alpha,
                top_k=top_k
            )
            
            retrieved_names = [os.path.basename(iems[idx][0]).replace(".csv", "") for idx, _, _, _, _ in results]
            
            # Calculate Precision@3
            hits = sum(1 for name in retrieved_names if name in expected_iems)
            precision = hits / top_k
            print(f"  Alpha={alpha:.1f} -> Precision@{top_k}: {precision:.2f} | Retrieved: {retrieved_names}")

if __name__ == "__main__":
    main()
