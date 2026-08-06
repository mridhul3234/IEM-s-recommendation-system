"""
normalize.py

Loads a raw frequency-response (FR) measurement and a target curve, then
computes the measured curve's deviation from that target.

Why this step exists:
Two IEMs measured by two different reviewers on two different rigs are NOT
directly comparable in absolute dB -- rig coupler shape, insertion depth,
and calibration all shift the raw curve up/down and side to side. What IS
comparable is how far each curve deviates from a shared reference target
(e.g. the Harman in-ear 2019 curve) at each frequency. That deviation curve
is what every downstream feature/embedding step in this project operates on.

This module is intentionally rig-agnostic: it resamples both the measurement
and the target onto a common log-spaced frequency grid via interpolation,
so it still works even if you later mix in data from a source (e.g.
Crinacle's raw 711/5128 rig files) that doesn't share oratory1990's exact
20 Hz-20 kHz, 695-point grid.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass

import numpy as np


@dataclass
class FRCurve:
    name: str
    freq: np.ndarray  # Hz, ascending
    db: np.ndarray  # raw measured dB (or deviation dB, once normalized)


def load_fr_csv(path: str, name: str | None = None) -> FRCurve:
    """Load a two-column (frequency, raw) CSV like the ones in AutoEq's
    measurements/ and targets/ folders."""
    freqs, dbs = [], []
    with open(path, newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert [h.strip().lower() for h in header[:2]] == ["frequency", "raw"], (
            f"Unexpected header {header} in {path}"
        )
        for row in reader:
            if not row:
                continue
            freqs.append(float(row[0]))
            dbs.append(float(row[1]))

    freq = np.array(freqs, dtype=float)
    db = np.array(dbs, dtype=float)

    # Some source files aren't perfectly sorted; sort defensively.
    order = np.argsort(freq)
    freq, db = freq[order], db[order]

    if name is None:
        import os
        name = os.path.splitext(os.path.basename(path))[0]
    return FRCurve(name=name, freq=freq, db=db)


def resample_to_grid(curve: FRCurve, grid_hz: np.ndarray) -> np.ndarray:
    """Interpolate a curve onto an arbitrary frequency grid using linear
    interpolation in log-frequency space (standard practice for FR data,
    since the ear -- and every target curve -- works in log-frequency,
    not linear Hz)."""
    log_src = np.log10(curve.freq)
    log_grid = np.log10(grid_hz)
    return np.interp(log_grid, log_src, curve.db, left=curve.db[0], right=curve.db[-1])


def standard_grid(n_points: int = 300, f_min: float = 20.0, f_max: float = 20000.0) -> np.ndarray:
    """A log-spaced frequency grid used as the common basis for every
    curve in this project, regardless of what grid the source file shipped
    with."""
    return np.logspace(np.log10(f_min), np.log10(f_max), n_points)


def deviation_from_target(measurement: FRCurve, target: FRCurve, grid_hz: np.ndarray | None = None):
    """Return (grid_hz, deviation_db) where deviation_db = measurement - target,
    both resampled onto the same grid first.

    A positive value at some frequency means the IEM is louder there than
    the target (e.g. positive deviation in the bass band = more bass than
    a Harman-neutral listener would expect); negative means quieter.
    """
    if grid_hz is None:
        grid_hz = standard_grid()

    m = resample_to_grid(measurement, grid_hz)
    t = resample_to_grid(target, grid_hz)

    # Align overall level: FR measurements are typically normalized to
    # ~0 dB around a reference band (commonly ~500 Hz-1 kHz) before
    # comparing shape, otherwise a curve that's just "measured 2 dB
    # quieter overall" looks like a bass-light, treble-light IEM when it
    # isn't. We anchor both curves to 0 dB at 1 kHz before subtracting.
    def anchor(vals, freqs):
        idx = np.argmin(np.abs(freqs - 1000.0))
        return vals - vals[idx]

    m_anchored = anchor(m, grid_hz)
    t_anchored = anchor(t, grid_hz)

    deviation = m_anchored - t_anchored
    return grid_hz, deviation
