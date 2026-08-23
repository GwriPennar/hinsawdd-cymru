"""Unit tests for Project 007 analysis helpers."""
from __future__ import annotations

import numpy as np

from analysis import ocean_mean_from_lat_sst


def test_ocean_mean_weights_latitude():
    lat = np.array([51.5, 52.5, 53.5])
    sst = np.array([10.0, 12.0, 14.0])
    mean = ocean_mean_from_lat_sst(lat, sst)
    w = np.cos(np.deg2rad(lat))
    expected = float(np.sum(sst * w) / np.sum(w))
    assert abs(mean - expected) < 1e-6
