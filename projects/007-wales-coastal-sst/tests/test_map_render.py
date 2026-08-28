"""Unit tests for Project 007 map helpers."""
from __future__ import annotations

import numpy as np
import pandas as pd

from map_render import grid_to_pivot, thin_grid


def test_thin_grid_reduces_large_grid():
    lats = np.arange(51.2, 53.6, 0.02)
    lons = np.arange(-6.5, -2.6, 0.02)
    rows = [
        {"latitude": lat, "longitude": lon, "anomaly_c": lat + lon}
        for lat in lats
        for lon in lons
    ]
    grid = pd.DataFrame(rows)
    assert len(grid) > 5000
    thinned = thin_grid(grid, step=3)
    assert len(thinned) < len(grid)
    assert thinned["latitude"].nunique() == len(sorted(grid["latitude"].unique())[::3])


def test_grid_to_pivot_shape():
    grid = pd.DataFrame(
        {
            "latitude": [51.0, 51.0, 52.0, 52.0],
            "longitude": [-6.0, -5.0, -6.0, -5.0],
            "anomaly_c": [1.0, 2.0, 3.0, 4.0],
        }
    )
    pivot = grid_to_pivot(grid, "anomaly_c")
    assert pivot.shape == (2, 2)
    assert pivot.loc[51.0, -6.0] == 1.0
