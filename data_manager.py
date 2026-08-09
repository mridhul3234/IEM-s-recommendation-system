"""
data_manager.py

Handles loading, parsing, and caching of the local fallback IEM dataset.
"""

import glob
import os
import numpy as np

from describe import describe
from features import extract_features, to_vector
from normalize import deviation_from_target, load_fr_csv, standard_grid
from embed import embed_texts

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET_PATH = os.path.join(HERE, "sample_data", "targets", "Harman in-ear 2019.csv")
IEM_DIR = os.path.join(HERE, "sample_data", "in-ear")

class DataManager:
    def __init__(self):
        self.target = None
        self.grid = None
        self.iems = []
        self.descriptions = []
        self.corpus_vectors = None
        self.corpus_embeddings = None

    def load_local_data(self):
        print("Loading local fallback data...")
        self.target = load_fr_csv(TARGET_PATH, name="Harman in-ear 2019")
        self.grid = standard_grid()
        
        iem_paths = sorted(glob.glob(os.path.join(IEM_DIR, "*.csv")))
        
        corpus_vectors_list = []
        
        for path in iem_paths:
            iem = load_fr_csv(path)
            freq, deviation = deviation_from_target(iem, self.target, grid_hz=self.grid)
            feats = extract_features(freq, deviation)
            iem_name_clean = os.path.basename(path).replace(".csv", "")
            desc = describe(feats, iem_name=iem_name_clean)
            
            # Inject deterministic mock price for testing
            mock_price = (sum(ord(c) for c in iem_name_clean) % 500) + 49
            feats["price"] = mock_price
            
            self.iems.append((iem_name_clean, feats))
            self.descriptions.append(desc)
            corpus_vectors_list.append(to_vector(feats))

            # Create some artificial variations so the dataset is larger than 8 items
            variants = [
                (" Pro", 1.2, 80),
                (" MkII", 0.9, -30)
            ]
            
            for suffix, feat_mult, price_adj in variants:
                var_name = iem_name_clean + suffix
                var_feats = {k: v * feat_mult if isinstance(v, (int, float)) else v for k, v in feats.items()}
                var_feats["price"] = max(20, mock_price + price_adj)
                var_desc = desc + f" This is the {suffix.strip()} variant, offering a slightly altered signature."
                self.iems.append((var_name, var_feats))
                self.descriptions.append(var_desc)
                corpus_vectors_list.append(to_vector(var_feats))

        self.corpus_vectors = np.array(corpus_vectors_list)
        self.corpus_embeddings = embed_texts(self.descriptions)
        print("Local fallback data loaded.")

# Singleton instance
data_manager = DataManager()
