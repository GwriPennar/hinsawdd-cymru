from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent


def add_location_links(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    lat = pd.to_numeric(out["latitude"], errors="raise")
    lon = pd.to_numeric(out["longitude"], errors="raise")
    out["coordinate"] = [f"{a:.5f}, {b:.5f}" for a, b in zip(lat, lon)]
    out["openstreetmap_url"] = [f"https://www.openstreetmap.org/?mlat={a:.5f}&mlon={b:.5f}#map=15/{a:.5f}/{b:.5f}" for a, b in zip(lat, lon)]
    out["google_maps_url"] = [f"https://www.google.com/maps?q={a:.5f},{b:.5f}" for a, b in zip(lat, lon)]
    out["location_precision_note"] = "thermal-anomaly cluster centroid; not a confirmed fire origin"
    return out
