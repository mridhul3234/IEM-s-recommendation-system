"""
generate_descriptions.py

Batch-generates LLM descriptions for all IEMs in the sample data folder.
Run this script once to populate the descriptions_cache.json offline.

Usage:
    set GEMINI_API_KEY=your_key
    python generate_descriptions.py
"""

import glob
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.describe import describe
from backend.features import extract_features
from backend.normalize import deviation_from_target, load_fr_csv, standard_grid

TARGET_PATH = PROJECT_ROOT / "data" / "sample_data" / "targets" / "Harman in-ear 2019.csv"
IEM_DIR = PROJECT_ROOT / "data" / "sample_data" / "in-ear"

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        
    if not os.environ.get("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY environment variable must be set.")
        sys.exit(1)

    target = load_fr_csv(TARGET_PATH, name="Harman in-ear 2019")
    grid = standard_grid()
    
    iem_paths = sorted(glob.glob(str(IEM_DIR / "*.csv")))
    if not iem_paths:
        print("No IEM data found.")
        sys.exit(1)
        
    print(f"Batch generating descriptions for {len(iem_paths)} IEMs...")
    
    for path in iem_paths:
        iem = load_fr_csv(path)
        freq, deviation = deviation_from_target(iem, target, grid_hz=grid)
        feats = extract_features(freq, deviation)
        
        iem_name = os.path.basename(path).replace(".csv", "")
        
        print(f"Generating for {iem_name}...")
        # describe() will automatically hit the API if not in cache, and save to cache
        desc = describe(feats, iem_name=iem_name)
        print(f"  Result: {desc}")

    print("Done. Cache populated.")

if __name__ == "__main__":
    main()
