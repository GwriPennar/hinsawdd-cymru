from pathlib import Path
import importlib.util
import pandas as pd

MODULE = Path(__file__).resolve().parents[1] / "corroboration.py"
spec = importlib.util.spec_from_file_location("corroboration", MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _cluster(**overrides):
    row = {
        "incident_id": "HC-TEST-1",
        "latitude": 51.772,
        "longitude": -3.086,
        "first_detected_utc": "2026-08-13T10:00:00Z",
        "last_detected_utc": "2026-08-13T14:00:00Z",
        "detection_count": 12,
        "peak_frp_mw": 20,
    }
    row.update(overrides)
    return pd.DataFrame([row])


def _external(start="2026-08-13T09:00:00Z", end="2026-08-13T15:00:00Z", source_class="fire_service"):
    return pd.DataFrame([{
        "external_incident_id": "EXT-1",
        "incident_name": "Test wildfire",
        "latitude": 51.773,
        "longitude": -3.087,
        "incident_start_utc": pd.Timestamp(start),
        "incident_end_utc": pd.Timestamp(end),
        "source_class": source_class,
        "source_name": "Test Fire Service",
        "source_url": "https://example.invalid/incident",
        "source_statement": "test",
    }])


def test_haversine_nearby():
    assert mod.haversine_km(51.772, -3.086, 51.773, -3.087) < 1


def test_official_current_match_requires_time_and_distance():
    out, matches = mod.correlate(_cluster(), _external(), radius_km=12)
    assert len(matches) == 1
    assert out.iloc[0].external_status == "official_current_match"


def test_recent_site_is_not_current_confirmation():
    external = _external(start="2026-07-19T10:00:00Z", end="2026-07-27T10:00:00Z")
    out, _ = mod.correlate(_cluster(), external, radius_km=12)
    assert out.iloc[0].external_status == "known_recent_wildfire_site"


def test_absence_of_external_match_stays_unknown_not_negative():
    external = _external()
    external["latitude"] = 53.0
    external["longitude"] = -4.5
    out, matches = mod.correlate(_cluster(), external, radius_km=12)
    assert matches.empty
    assert out.iloc[0].external_status == "no_current_match"
