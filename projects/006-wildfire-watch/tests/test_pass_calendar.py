"""Tests for VIIRS pass calendar status logic (no live TLE required)."""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

import pass_calendar as pc  # noqa: E402


def _cal(passes: list[dict]) -> dict:
    return {"passes": passes, "generated_at_utc": "2026-08-16T03:00:00+00:00"}


def test_status_quiet_until_pass():
    cal = _cal(
        [
            {
                "site": "wales",
                "sat_label": "NOAA20",
                "culmination_utc": "2026-08-16T13:40:00+00:00",
                "elev_deg": 42.0,
                "nadir_km": 180.0,
                "minutes_from_now": 640.0,
            }
        ]
    )
    st = pc.status_message(cal, site="wales", now=datetime(2026, 8, 16, 3, 0, tzinfo=timezone.utc))
    assert st["mode"] == "quiet_until_pass"
    assert "13:40" in st["line"]
    assert "Quiet because no useful pass" in st["line"]


def test_status_firms_lag_window():
    cal = _cal(
        [
            {
                "site": "gower",
                "sat_label": "SNPP",
                "culmination_utc": "2026-08-16T02:15:00+00:00",
                "elev_deg": 55.0,
                "nadir_km": 90.0,
                "minutes_from_now": -45.0,
            }
        ]
    )
    st = pc.status_message(
        cal,
        site="gower",
        firms_latest_obs_utc="2026-08-15 13:46:00+00:00",
        now=datetime(2026, 8, 16, 3, 0, tzinfo=timezone.utc),
    )
    assert st["mode"] == "firms_lag_window"
    assert "waiting on FIRMS" in st["line"]
    assert "13:46" in st["line"]


def test_status_pass_opening_soon():
    cal = _cal(
        [
            {
                "site": "wales",
                "sat_label": "NOAA21",
                "culmination_utc": "2026-08-16T03:40:00+00:00",
                "elev_deg": 28.0,
                "nadir_km": 400.0,
                "minutes_from_now": 40.0,
            }
        ]
    )
    st = pc.status_message(cal, site="wales", now=datetime(2026, 8, 16, 3, 0, tzinfo=timezone.utc))
    assert st["mode"] == "pass_opening_soon"
    assert "opening soon" in st["line"]


def test_haversine_zero():
    assert pc.haversine_km(52.3, -3.8, 52.3, -3.8) == 0.0
