from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.image as mpimg
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

import scientific_map as sm  # noqa: E402


def _boundary() -> dict:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name_en": "Test community"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-5.6, 51.2],
                        [-2.55, 51.2],
                        [-2.55, 53.5],
                        [-5.6, 53.5],
                        [-5.6, 51.2],
                    ]],
                },
            }
        ],
    }


def _incidents() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "incident_id": "HC-TA-1",
                "latitude": 51.62,
                "longitude": -3.94,
                "detection_count": 1,
                "satellite_count": 1,
                "satellites": "N",
                "sources": "VIIRS_SNPP_NRT",
                "first_detected_utc": "2026-08-13T02:34:00+00:00",
                "last_detected_utc": "2026-08-13T02:34:00+00:00",
                "duration_hours": 0.0,
                "peak_frp_mw": 0.35,
                "mean_frp_mw": 0.35,
                "max_confidence": "nominal",
                "daynight": "N",
                "in_wales_watch_bbox": True,
            },
            {
                "incident_id": "HC-TA-2",
                "latitude": 52.10,
                "longitude": -3.78,
                "detection_count": 25,
                "satellite_count": 3,
                "satellites": "N, N20, N21",
                "sources": "VIIRS_NOAA20_NRT, VIIRS_NOAA21_NRT, VIIRS_SNPP_NRT",
                "first_detected_utc": "2026-08-12T12:00:00+00:00",
                "last_detected_utc": "2026-08-13T14:00:00+00:00",
                "duration_hours": 26.0,
                "peak_frp_mw": 40.0,
                "mean_frp_mw": 10.0,
                "max_confidence": "high",
                "daynight": "D,N",
                "in_wales_watch_bbox": True,
            },
        ]
    )


def test_satellite_evidence_band_is_not_wildfire_probability():
    incidents = _incidents()
    assert sm.satellite_evidence_band(incidents.iloc[0]) == "low"
    assert sm.satellite_evidence_band(incidents.iloc[1]) == "strong satellite evidence"


def test_candidate_table_uses_boundary_and_community_name():
    table = sm.build_candidate_table(_incidents(), _boundary())
    assert len(table) == 2
    assert set(table["community_name"]) == {"Test community"}
    assert set(table["external_confirmation_status"]) == {"not assessed"}


def test_boundary_fixture_provenance_and_render_dimensions(tmp_path: Path):
    boundary_path = tmp_path / "boundary.geojson"
    boundary_path.write_text(json.dumps(_boundary()))
    boundary, manifest = sm.fetch_or_load_boundary(boundary_path, tmp_path)
    assert manifest["mode"] == "retained_fixture"
    assert manifest["dataset"] == "Communities (Wales)"

    candidates = sm.build_candidate_table(_incidents(), boundary)
    summary = {
        "generated_at_utc": "2026-08-13T18:19:34+00:00",
        "latest_detection_utc": "2026-08-13T14:22:00+00:00",
    }
    figures = tmp_path / "figures"
    sm.render_dark_map(candidates, boundary, manifest, summary, figures, square=False)
    sm.render_dark_map(candidates, boundary, manifest, summary, figures, square=True)

    wide = mpimg.imread(figures / "wales_wildfire_watch_dark.png")
    square = mpimg.imread(figures / "wales_wildfire_watch_dark_square.png")
    assert wide.shape[:2] == (900, 1600)
    assert square.shape[:2] == (1080, 1080)
    assert (figures / "wales_wildfire_watch_dark.svg").stat().st_size > 0
    assert (figures / "wales_wildfire_watch_dark_square.svg").stat().st_size > 0
