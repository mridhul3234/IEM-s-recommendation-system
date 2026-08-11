"""
data_manager.py

Handles loading, parsing, and caching of the local fallback IEM dataset.
"""

import glob
import logging
import os
import numpy as np

from describe import describe
from features import extract_features, to_vector
from normalize import deviation_from_target, load_fr_csv, standard_grid
from embed import embed_texts

logger = logging.getLogger(__name__)

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET_PATH = os.path.join(HERE, "sample_data", "targets", "Harman in-ear 2019.csv")
IEM_DIR = os.path.join(HERE, "sample_data", "in-ear")

# Artificial variants added so the local dataset has enough items for
# meaningful ranking without real Supabase data.
_VARIANTS = [
    (" Pro",  1.2,  80),
    (" MkII", 0.9, -30),
]


class DataManager:
    def __init__(self):
        self.target = None
        self.grid = None
        self.iems: list[tuple[str, dict]] = []
        self.descriptions: list[str] = []
        self.corpus_vectors: np.ndarray | None = None
        self.corpus_embeddings: np.ndarray | None = None

    def load_local_data(self) -> None:
        logger.info("Loading local fallback data...")
        self.target = load_fr_csv(TARGET_PATH, name="Harman in-ear 2019")
        self.grid = standard_grid()

        iem_paths = sorted(glob.glob(os.path.join(IEM_DIR, "*.csv")))
        if not iem_paths:
            logger.warning("No IEM CSV files found in %s", IEM_DIR)

        corpus_vectors_list: list[np.ndarray] = []

        for path in iem_paths:
            iem = load_fr_csv(path)
            freq, deviation = deviation_from_target(iem, self.target, grid_hz=self.grid)
            feats = extract_features(freq, deviation)
            iem_name = os.path.basename(path).replace(".csv", "")
            desc = describe(feats, iem_name=iem_name)

            # Deterministic mock price — replaced by real data in production.
            mock_price = (sum(ord(c) for c in iem_name) % 500) + 49
            feats["price"] = mock_price

            self.iems.append((iem_name, feats))
            self.descriptions.append(desc)
            corpus_vectors_list.append(to_vector(feats))

            for suffix, feat_mult, price_adj in _VARIANTS:
                var_name = iem_name + suffix
                var_feats = {
                    k: round(v * feat_mult, 2) if isinstance(v, (int, float)) else v
                    for k, v in feats.items()
                }
                var_feats["price"] = max(20, mock_price + price_adj)
                var_desc = (
                    desc
                    + f" This is the {suffix.strip()} variant,"
                    + " offering a slightly altered signature."
                )
                self.iems.append((var_name, var_feats))
                self.descriptions.append(var_desc)
                corpus_vectors_list.append(to_vector(var_feats))

        self.corpus_vectors = np.array(corpus_vectors_list)
        self.corpus_embeddings = embed_texts(self.descriptions)
        logger.info("Local fallback data loaded (%d IEMs).", len(self.iems))


# Singleton instance
data_manager = DataManager()
