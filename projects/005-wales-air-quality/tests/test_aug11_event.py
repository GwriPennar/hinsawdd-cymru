from __future__ import annotations

import struct
import sys
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from aug11_event import build_aug11_event_summary, render_event_chart


def _png_dimensions(path: Path):
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", data[16:24])


def synthetic_hourly() -> pd.DataFrame:
    rows = []
    prior = pd.date_range("2025-08-12 00:00", periods=20, freq="h", tz="UTC")
    for timestamp in prior:
        rows.append(
            {
                "timestamp": timestamp,
                "reporting_date": timestamp.floor("D"),
                "station_code": "SWA1",
                "station_name": "Swansea Roadside",
                "site_type": "Urban Traffic",
                "pm25": 20.0,
                "pm25_screened": 20.0,
                "pm10": 25.0,
                "no2": 5.0,
            }
        )
    for hour, value in enumerate([51.0, 10.0, 27.0, 27.0, 47.0, 48.0]):
        timestamp = pd.Timestamp("2026-08-11 00:00", tz="UTC") + pd.Timedelta(hours=hour)
        rows.append(
            {
                "timestamp": timestamp,
                "reporting_date": pd.Timestamp("2026-08-11", tz="UTC"),
                "station_code": "SWA1",
                "station_name": "Swansea Roadside",
                "site_type": "Urban Traffic",
                "pm25": value,
                "pm25_screened": value,
                "pm10": value + 2.0,
                "no2": 6.0,
            }
        )
    for station_code, name, offset in [
        ("CARD", "Cardiff Centre", 0.0),
        ("PT4", "Port Talbot Margam", 8.0),
    ]:
        for hour in range(13):
            timestamp = pd.Timestamp("2026-08-11 00:00", tz="UTC") + pd.Timedelta(hours=hour)
            rows.append(
                {
                    "timestamp": timestamp,
                    "reporting_date": pd.Timestamp("2026-08-11", tz="UTC"),
                    "station_code": station_code,
                    "station_name": name,
                    "site_type": "Urban Background",
                    "pm25": 5.0 + offset + hour / 4,
                    "pm25_screened": 5.0 + offset + hour / 4,
                    "pm10": 10.0 + offset,
                    "no2": 4.0,
                }
            )
    return pd.DataFrame(rows)


def test_aug11_summary_uses_physical_clock_and_prior_p95():
    result = build_aug11_event_summary(synthetic_hourly())
    swansea = result[result["station_code"] == "SWA1"].iloc[0]
    assert swansea["valid_hours"] == 6
    assert swansea["event_pm25_mean"] == 35.0
    assert swansea["event_pm25_max"] == 51.0
    assert swansea["prior_365d_hourly_pm25_p95"] == 20.0
    assert swansea["hours_at_or_above_prior_p95"] == 5


def test_aug11_chart_dimensions(tmp_path):
    hourly = synthetic_hourly()
    wide = tmp_path / "wales_aurn_pm25_aug11_smoke_window_dark"
    square = tmp_path / "wales_aurn_pm25_aug11_smoke_window_dark_square"
    render_event_chart(hourly, wide, square=False)
    render_event_chart(hourly, square, square=True)
    assert _png_dimensions(wide.with_suffix(".png")) == (1600, 900)
    assert _png_dimensions(square.with_suffix(".png")) == (1080, 1080)
    assert wide.with_suffix(".svg").exists()
    assert square.with_suffix(".svg").exists()
