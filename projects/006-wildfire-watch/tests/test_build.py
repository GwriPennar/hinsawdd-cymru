from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import requests

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

import build  # noqa: E402


def _load_fixture() -> pd.DataFrame:
    frames = []
    for path in sorted((PROJECT_DIR / "tests" / "fixtures").glob("VIIRS_*_NRT.csv")):
        frames.append(build.parse_and_normalize(path.read_bytes(), path.stem))
    return pd.concat(frames, ignore_index=True)


def test_parse_and_normalize_uses_utc_and_confidence_labels():
    path = PROJECT_DIR / "tests" / "fixtures" / "VIIRS_SNPP_NRT.csv"
    frame = build.parse_and_normalize(path.read_bytes(), "VIIRS_SNPP_NRT")
    assert str(frame.loc[0, "acq_datetime_utc"].tzinfo) == "UTC"
    assert frame.loc[0, "acq_datetime_utc"].hour == 2
    assert set(frame["confidence_label"]) == {"low", "nominal", "high"}
    assert frame["in_wales_watch_bbox"].sum() == 3


def test_cluster_groups_nearby_cross_satellite_detections():
    frame = _load_fixture()
    clustered = build.cluster_detections(frame, distance_km=5.0, time_hours=18.0)
    swansea = clustered[(clustered["latitude"] > 51.61) & (clustered["latitude"] < 51.63)]
    assert swansea["cluster_id"].nunique() == 1
    assert len(swansea) == 4
    assert clustered["cluster_id"].nunique() == 5


def test_incident_summary_keeps_evidence_boundary_fields():
    incidents = build.summarize_incidents(build.cluster_detections(_load_fixture()))
    swansea = incidents.loc[incidents["detection_count"].idxmax()]
    assert swansea["detection_count"] == 4
    assert swansea["satellite_count"] == 3
    assert swansea["max_confidence"] == "high"
    assert swansea["in_wales_watch_bbox"]
    assert swansea["incident_id"].startswith("HC-TA-20260812-")


def test_build_outputs_writes_geojson_summary_and_map(tmp_path: Path):
    summary = build.build_outputs(_load_fixture(), tmp_path)
    assert summary["detection_count"] == 8
    assert summary["incident_count"] == 5
    assert summary["wales_watch_incident_count"] == 2

    geojson = json.loads((tmp_path / "data" / "derived" / "incidents.geojson").read_text())
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == 5

    site = (tmp_path / "site" / "index.html").read_text()
    assert "Hinsawdd Cymru: Wildfire Watch" in site
    assert "not a confirmed wildfire" in site
    assert "leaflet.markercluster" in site
    assert "MAP_KEY" not in site


def test_request_failures_do_not_expose_map_key():
    secret = "synthetic-secret-map-key"

    class BrokenSession:
        def get(self, url, timeout):
            raise requests.Timeout(f"timeout while requesting {url}")

    try:
        build.fetch_firms_csv(
            BrokenSession(), secret, "VIIRS_SNPP_NRT", build.UK_BBOX, 2
        )
    except RuntimeError as exc:
        assert secret not in str(exc)
        assert "Timeout" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError")


def test_retained_loader_rejects_empty_directory(tmp_path: Path):
    try:
        build.load_retained_csvs(tmp_path)
    except FileNotFoundError as exc:
        assert "No retained" in str(exc)
    else:
        raise AssertionError("Expected FileNotFoundError")
