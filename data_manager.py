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

            # Only data derived from the checked-in measurement is exposed by
            # the offline dataset.  In particular, do not invent prices or
            # product variants: an unknown price must remain unknown.
            feats["acoustic_profile_source"] = "local_measurement"

            self.iems.append((iem_name, feats))
            self.descriptions.append(desc)
            corpus_vectors_list.append(to_vector(feats))

        self.corpus_vectors = np.array(corpus_vectors_list, dtype=float)
        self.corpus_embeddings = embed_texts(self.descriptions)
        logger.info("Local fallback data loaded (%d IEMs).", len(self.iems))


# Singleton instance
data_manager = DataManager()
