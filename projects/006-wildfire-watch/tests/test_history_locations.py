from __future__ import annotations

import importlib.util
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_location_links_are_coordinate_driven():
    module = load_module("location_links", "location_links.py")
    frame = pd.DataFrame([{"latitude": 51.64457, "longitude": -3.93045}])
    out = module.add_location_links(frame)
    assert out.loc[0, "coordinate"] == "51.64457, -3.93045"
    assert "51.64457" in out.loc[0, "openstreetmap_url"]
    assert "-3.93045" in out.loc[0, "google_maps_url"]
    assert "not a confirmed fire origin" in out.loc[0, "location_precision_note"]


def test_history_dedupe_preserves_unique_observations():
    module = load_module("history", "history.py")
    frame = pd.DataFrame([
        {"source": "VIIRS_SNPP_NRT", "satellite": "N", "acq_datetime_utc": "2026-08-13T12:00:00Z", "latitude": 51.5, "longitude": -3.5},
        {"source": "VIIRS_SNPP_NRT", "satellite": "N", "acq_datetime_utc": "2026-08-13T12:00:00Z", "latitude": 51.5, "longitude": -3.5},
        {"source": "VIIRS_NOAA20_NRT", "satellite": "1", "acq_datetime_utc": "2026-08-13T12:00:00Z", "latitude": 51.5, "longitude": -3.5},
    ])
    out = module._dedupe(frame)
    assert len(out) == 2
