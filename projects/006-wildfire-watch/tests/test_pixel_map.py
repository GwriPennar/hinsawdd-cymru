from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.image as mpimg
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

import pixel_map as pm  # noqa: E402
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


def _detections() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "latitude": 51.62,
                "longitude": -3.94,
                "acq_datetime_utc": "2026-08-13T02:34:00+00:00",
                "satellite": "N",
                "confidence_label": "nominal",
                "frp": 1.2,
                "source": "VIIRS_SNPP_NRT",
            },
            {
                "latitude": 52.10,
                "longitude": -3.78,
                "acq_datetime_utc": "2026-08-13T14:00:00+00:00",
                "satellite": "N20",
                "confidence_label": "high",
                "frp": 12.0,
                "source": "VIIRS_NOAA20_NRT",
            },
            {
                "latitude": 51.5,
                "longitude": 0.1,
                "acq_datetime_utc": "2026-08-13T12:00:00+00:00",
                "satellite": "N21",
                "confidence_label": "low",
                "frp": 0.4,
                "source": "VIIRS_NOAA21_NRT",
            },
        ]
    )


def test_detections_inside_wales_keeps_only_boundary_pixels():
    pixels = pm.detections_inside_wales(_detections(), _boundary(), [-5.6, 51.2, -2.55, 53.5])
    assert len(pixels) == 2
    assert set(pixels["community_name"]) == {"Test community"}
    assert set(pixels["confidence_label"]) == {"nominal", "high"}


def test_pixel_map_render_dimensions(tmp_path: Path):
    boundary_path = tmp_path / "boundary.geojson"
    boundary_path.write_text(json.dumps(_boundary()))
    boundary, manifest = sm.fetch_or_load_boundary(boundary_path, tmp_path)
    pixels = pm.detections_inside_wales(_detections(), boundary, manifest["extent"])
    summary = {
        "generated_at_utc": "2026-08-13T18:19:34+00:00",
        "latest_detection_utc": "2026-08-13T14:22:00+00:00",
    }
    figures = tmp_path / "figures"
    pm.render_pixel_map(pixels, boundary, manifest, summary, figures, square=False)
    pm.render_pixel_map(pixels, boundary, manifest, summary, figures, square=True)

    wide = mpimg.imread(figures / "wales_firms_pixels_dark.png")
    square = mpimg.imread(figures / "wales_firms_pixels_dark_square.png")
    assert wide.shape[:2] == (1800, 3200)
    assert square.shape[:2] == (2160, 2160)
    assert (figures / "wales_firms_pixels_dark.svg").stat().st_size > 0
