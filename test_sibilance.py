import glob, os, numpy as np
from normalize import load_fr_csv, standard_grid, deviation_from_target
from features import _band_mask, SIBILANCE_BAND

target = load_fr_csv('sample_data/targets/Harman in-ear 2019.csv')
grid = standard_grid()

for p in glob.glob('sample_data/in-ear/*.csv'):
    f, d = deviation_from_target(load_fr_csv(p), target, grid)
    m = _band_mask(f, *SIBILANCE_BAND)
    base = float(np.mean(d[_band_mask(f, 2000, 5000)]))
    peak = float(np.max(d[m]))
    risk1 = round(max(0.0, peak - base), 2)
    risk2 = round(max(0.0, peak - base) if peak > 0 else 0.0, 2)
    risk3 = round(max(0.0, peak - max(0.0, base)), 2) # Penalize peak if base is negative?
    
    print(f"{os.path.basename(p):<30} Old Risk: {risk1:<5} | New Risk: {risk2:<5} | Peak: {peak:5.2f} | Base: {base:5.2f}")
