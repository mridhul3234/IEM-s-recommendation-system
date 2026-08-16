import glob, os, sys, numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from acousticsearch.features import _band_mask, SIBILANCE_BAND
from acousticsearch.normalize import load_fr_csv, standard_grid, deviation_from_target

target = load_fr_csv(PROJECT_ROOT / 'data' / 'sample_data' / 'targets' / 'Harman in-ear 2019.csv')
grid = standard_grid()

for p in glob.glob(str(PROJECT_ROOT / 'data' / 'sample_data' / 'in-ear' / '*.csv')):
    f, d = deviation_from_target(load_fr_csv(p), target, grid)
    m = _band_mask(f, *SIBILANCE_BAND)
    base = float(np.mean(d[_band_mask(f, 2000, 5000)]))
    peak = float(np.max(d[m]))
    risk1 = round(max(0.0, peak - base), 2)
    risk2 = round(max(0.0, peak - base) if peak > 0 else 0.0, 2)
    risk3 = round(max(0.0, peak - max(0.0, base)), 2) # Penalize peak if base is negative?
    
    print(f"{os.path.basename(p):<30} Old Risk: {risk1:<5} | New Risk: {risk2:<5} | Peak: {peak:5.2f} | Base: {base:5.2f}")
