"""
run_demo.py

End-to-end sanity check for the normalize -> features -> describe pipeline,
run against a handful of real IEM measurements (sourced from AutoEq's
open-source measurement database, see README.md for attribution).

Run:
    python3 run_demo.py
"""

from __future__ import annotations

import glob
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from acousticsearch.describe import describe
from acousticsearch.features import extract_features
from acousticsearch.normalize import deviation_from_target, load_fr_csv, standard_grid

TARGET_PATH = PROJECT_ROOT / "data" / "sample_data" / "targets" / "Harman in-ear 2019.csv"
IEM_DIR = PROJECT_ROOT / "data" / "sample_data" / "in-ear"


def main():
    target = load_fr_csv(TARGET_PATH, name="Harman in-ear 2019")
    grid = standard_grid()

    iem_paths = sorted(glob.glob(str(IEM_DIR / "*.csv")))
    print(f"Loaded target: {target.name}")
    print(f"Found {len(iem_paths)} sample IEMs\n")

    rows = []
    for path in iem_paths:
        iem = load_fr_csv(path)
        freq, deviation = deviation_from_target(iem, target, grid_hz=grid)
        feats = extract_features(freq, deviation)
        rows.append((iem.name, feats))

    # --- Feature table ---
    band_cols = ["sub_bass", "bass", "low_mids", "mids", "presence", "treble", "air"]
    derived_cols = ["sibilance_risk", "tonal_tilt", "bass_to_treble"]

    name_w = max(len(name) for name, _ in rows) + 2
    header = f"{'IEM':<{name_w}}" + "".join(f"{c:>10}" for c in band_cols) + "".join(
        f"{c:>16}" for c in derived_cols
    )
    print(header)
    print("-" * len(header))
    for name, feats in rows:
        line = f"{name:<{name_w}}" + "".join(f"{feats[c]:>10.2f}" for c in band_cols)
        line += "".join(f"{feats[c]:>16.2f}" for c in derived_cols)
        print(line)

    # --- Generated descriptions (rule-based placeholder for the LLM step) ---
    print("\n--- Generated tonal descriptions ---")
    for name, feats in rows:
        clean_name = os.path.basename(name).replace(".csv", "")
        print(f"\n{clean_name}:")
        print(f"  {describe(feats, iem_name=clean_name)}")

    # --- Quick sanity check: which IEM is bassiest / brightest / most sibilant ---
    print("\n--- Sanity check (does the ranking make sense?) ---")
    bassiest = max(rows, key=lambda r: r[1]["bass"])
    brightest = max(rows, key=lambda r: r[1]["tonal_tilt"])
    most_sibilant = max(rows, key=lambda r: r[1]["sibilance_risk"])
    print(f"Bassiest relative to target : {bassiest[0]} ({bassiest[1]['bass']:+.2f} dB)")
    print(f"Brightest tonal tilt        : {brightest[0]} ({brightest[1]['tonal_tilt']:+.3f})")
    print(f"Highest sibilance risk      : {most_sibilant[0]} ({most_sibilant[1]['sibilance_risk']:.2f})")


if __name__ == "__main__":
    main()
