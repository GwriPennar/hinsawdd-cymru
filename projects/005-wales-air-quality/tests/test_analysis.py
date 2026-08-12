from __future__ import annotations

import struct
import sys
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from analysis import Station, daily_means, find_measurement_column, parse_uk_air_csv, select_windows
from charts import render_all_charts


def test_find_measurement_columns_ignores_status():
    columns = [
        "Date", "Time", "PM2.5 particulate matter (Hourly measured)",
        "Status PM2.5 particulate matter (Hourly measured)",
        "PM10 particulate matter (Hourly measured)", "Nitrogen dioxide", "Ozone",
    ]
    assert find_measurement_column(columns, "pm25") == "PM2.5 particulate matter (Hourly measured)"
    assert find_measurement_column(columns, "pm10") == "PM10 particulate matter (Hourly measured)"
    assert find_measurement_column(columns, "no2") == "Nitrogen dioxide"
    assert find_measurement_column(columns, "o3") == "Ozone"


def test_parser_handles_hour_24_and_numeric_missing_values():
    station = Station("TEST", "Test Site", "Urban Background", 51.5, -3.2)
    text = """Date,Time,PM2.5 particulate matter (Hourly measured),PM10 particulate matter (Hourly measured),Nitrogen dioxide,Ozone
11/08/2026,23:00,8.5,12.0,15.0,40.0
11/08/2026,24:00,No data,13.0,16.0,41.0
"""
    parsed = parse_uk_air_csv(text, station)
    assert len(parsed) == 2
    assert parsed.loc[1, "timestamp"] == pd.Timestamp("2026-08-12T00:00:00Z")
    assert parsed.loc[1, "reporting_date"] == pd.Timestamp("2026-08-11T00:00:00Z")
    assert pd.isna(parsed.loc[1, "pm25"])
    assert parsed.loc[0, "pm25"] == 8.5


def test_daily_mean_requires_18_valid_hours():
    station = Station("TEST", "Test Site", "Urban Background", 51.5, -3.2)
    timestamps = pd.date_range("2026-08-01", periods=48, freq="h", tz="UTC")
    hourly = pd.DataFrame({
        "timestamp": timestamps,
        "station_code": station.code,
        "station_name": station.name,
        "site_type": station.site_type,
        "latitude": station.latitude,
        "longitude": station.longitude,
        "pm25": [10.0] * 17 + [None] * 7 + [20.0] * 24,
        "pm10": [20.0] * 48,
        "no2": [5.0] * 48,
        "o3": [30.0] * 48,
    })
    daily = daily_means(hourly)
    first, second = daily.iloc[0], daily.iloc[1]
    assert pd.isna(first["pm25"])
    assert first["pm25_hours"] == 17
    assert second["pm25"] == 20.0
    assert second["pm25_hours"] == 24


def _png_dimensions(path: Path):
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", data[16:24])


def test_dark_chart_suite_dimensions(tmp_path):
    stations = [
        Station("A", "Alpha", "Urban Background", 51.48, -3.18),
        Station("B", "Beta", "Rural Background", 51.78, -4.69),
    ]
    dates = pd.date_range("2026-07-01", periods=40, freq="D", tz="UTC")
    rows = []
    for i, date in enumerate(dates):
        for j, station in enumerate(stations):
            rows.append({
                "date": date, "station_code": station.code, "station_name": station.name,
                "site_type": station.site_type, "latitude": station.latitude,
                "longitude": station.longitude, "pm25": 5.0 + j + (i % 7),
                "pm25_hours": 24, "pm10": 10.0, "pm10_hours": 24,
                "no2": 8.0, "no2_hours": 24, "o3": 35.0, "o3_hours": 24,
            })
    daily = pd.DataFrame(rows)
    latest, rolling_start, recent_start, _, _ = select_windows(daily, 30, 14)
    metadata = {
        "latest_observation_day_utc": latest.isoformat(),
        "rolling_start_utc": rolling_start.isoformat(),
        "recent_start_utc": recent_start.isoformat(),
        "rolling_days": 30,
        "recent_days": 14,
    }
    render_all_charts(daily, stations, metadata, tmp_path)

    stems = [
        "wales_aurn_pm25_rolling_year_dark", "wales_aurn_pm25_recent_dark",
        "wales_aurn_pm25_station_distribution_dark", "wales_aurn_pm25_station_map_dark",
    ]
    for stem in stems:
        assert _png_dimensions(tmp_path / f"{stem}.png") == (1600, 900)
        assert _png_dimensions(tmp_path / f"{stem}_square.png") == (1080, 1080)
        assert (tmp_path / f"{stem}.svg").exists()
        assert (tmp_path / f"{stem}_square.svg").exists()
