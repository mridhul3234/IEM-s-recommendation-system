"""
tests/test_normalize.py

Unit tests for normalize.py — load_fr_csv, resample_to_grid,
deviation_from_target, and standard_grid.
"""

import os
import tempfile
import numpy as np
import pytest

from backend.normalize import load_fr_csv, resample_to_grid, standard_grid, deviation_from_target, FRCurve


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_csv(path: str, rows: list[tuple]):
    with open(path, "w") as f:
        for freq, db in rows:
            f.write(f"{freq},{db}\n")


# ---------------------------------------------------------------------------
# standard_grid
# ---------------------------------------------------------------------------

class TestStandardGrid:
    def test_default_length(self):
        grid = standard_grid()
        assert len(grid) == 300

    def test_custom_length(self):
        grid = standard_grid(n_points=100)
        assert len(grid) == 100

    def test_range(self):
        grid = standard_grid()
        assert grid[0] == pytest.approx(20.0, rel=0.01)
        assert grid[-1] == pytest.approx(20000.0, rel=0.01)

    def test_ascending(self):
        grid = standard_grid()
        assert np.all(np.diff(grid) > 0)


# ---------------------------------------------------------------------------
# load_fr_csv
# ---------------------------------------------------------------------------

class TestLoadFrCsv:
    def test_basic_load(self, tmp_path):
        csv_path = tmp_path / "test.csv"
        write_csv(str(csv_path), [(20, -5), (100, 0), (1000, 2), (10000, -1)])
        curve = load_fr_csv(str(csv_path))
        assert curve.name == "test"
        assert len(curve.freq) == 4
        assert curve.freq[0] < curve.freq[-1]  # ascending

    def test_auto_name_from_path(self, tmp_path):
        csv_path = tmp_path / "SomeName IEM.csv"
        write_csv(str(csv_path), [(100, 0), (1000, 0)])
        curve = load_fr_csv(str(csv_path))
        assert curve.name == "SomeName IEM"

    def test_explicit_name(self, tmp_path):
        csv_path = tmp_path / "x.csv"
        write_csv(str(csv_path), [(100, 0)])
        curve = load_fr_csv(str(csv_path), name="Custom Name")
        assert curve.name == "Custom Name"

    def test_skips_invalid_rows(self, tmp_path):
        csv_path = tmp_path / "bad.csv"
        with open(str(csv_path), "w") as f:
            f.write("Frequency,SPL\n")  # header row (skipped as ValueError)
            f.write("100,5\n")
            f.write("200,3\n")
        curve = load_fr_csv(str(csv_path))
        assert len(curve.freq) == 2

    def test_logs_malformed_row_count(self, tmp_path, caplog):
        csv_path = tmp_path / "bad.csv"
        csv_path.write_text("100,5\nnot-a-number,2\n200,nan\n")
        curve = load_fr_csv(str(csv_path))
        assert len(curve.freq) == 1
        assert "Skipped 2 malformed row(s)" in caplog.text

    def test_unsorted_input_is_sorted(self, tmp_path):
        csv_path = tmp_path / "unsorted.csv"
        write_csv(str(csv_path), [(1000, 0), (200, 1), (50, -2)])
        curve = load_fr_csv(str(csv_path))
        assert np.all(np.diff(curve.freq) > 0)

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            load_fr_csv("/nonexistent/path.csv")

    def test_empty_file_returns_empty_arrays(self, tmp_path):
        csv_path = tmp_path / "empty.csv"
        csv_path.write_text("")
        curve = load_fr_csv(str(csv_path))
        assert len(curve.freq) == 0


# ---------------------------------------------------------------------------
# resample_to_grid
# ---------------------------------------------------------------------------

class TestResampleToGrid:
    def test_flat_curve_stays_flat(self):
        freq = np.array([20.0, 1000.0, 20000.0])
        db = np.array([3.0, 3.0, 3.0])
        curve = FRCurve(name="flat", freq=freq, db=db)
        grid = standard_grid()
        resampled = resample_to_grid(curve, grid)
        assert np.allclose(resampled, 3.0, atol=0.01)

    def test_output_length_matches_grid(self):
        freq = np.logspace(np.log10(20), np.log10(20000), 50)
        curve = FRCurve(name="x", freq=freq, db=np.zeros(50))
        grid = standard_grid(n_points=200)
        out = resample_to_grid(curve, grid)
        assert len(out) == 200


# ---------------------------------------------------------------------------
# deviation_from_target
# ---------------------------------------------------------------------------

class TestDeviationFromTarget:
    def _flat_curve(self, value: float, name: str = "test") -> FRCurve:
        freq = np.logspace(np.log10(20), np.log10(20000), 300)
        db = np.full(300, value)
        return FRCurve(name=name, freq=freq, db=db)

    def test_identical_curves_deviation_is_zero(self):
        curve = self._flat_curve(5.0)
        target = self._flat_curve(5.0, name="target")
        grid = standard_grid()
        freq, deviation = deviation_from_target(curve, target, grid)
        assert np.allclose(deviation, 0.0, atol=0.01)

    def test_shaped_deviation(self):
        """
        A measurement with elevated bass (relative to its own 1 kHz anchor)
        vs a flat target should produce a *positive* mean deviation in the
        bass band and a value near 0 in the mids.
        """
        freq = np.logspace(np.log10(20), np.log10(20000), 300)
        # measurement: +5 dB below 250 Hz, 0 everywhere else
        meas_db = np.where(freq < 250, 5.0, 0.0)
        target_db = np.zeros(300)
        measurement = FRCurve(name="meas", freq=freq, db=meas_db)
        target = FRCurve(name="target", freq=freq, db=target_db)
        grid = standard_grid()
        _, deviation = deviation_from_target(measurement, target, grid)
        bass_mask = (grid >= 60) & (grid < 250)
        mid_mask = (grid >= 500) & (grid < 2000)
        # Bass should be elevated, mids near neutral
        assert np.mean(deviation[bass_mask]) > 2.0
        assert abs(np.mean(deviation[mid_mask])) < 0.5

    def test_output_shape_matches_grid(self):
        m = self._flat_curve(0.0)
        t = self._flat_curve(0.0, name="target")
        grid = standard_grid(n_points=150)
        freq, deviation = deviation_from_target(m, t, grid)
        assert len(freq) == 150
        assert len(deviation) == 150

    def test_uses_default_grid_if_none(self):
        m = self._flat_curve(0.0)
        t = self._flat_curve(0.0, name="target")
        freq, deviation = deviation_from_target(m, t, grid_hz=None)
        assert len(freq) == 300  # default standard_grid length
