from __future__ import annotations

import struct
import sys
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from analysis import (
    Station,
    apply_pm25_qc,
    build_event_screen,
    build_period_comparison,
    build_site_relative_daily,
    build_site_relative_summary,
    daily_means,
    find_measurement_column,
    parse_uk_air_csv,
    select_windows,
)
from charts import render_all_charts


def test_find_measurement_columns_ignores_status():
    columns = [
        "Date",
        "Time",
        "PM2.5 particulate matter (Hourly measured)",
        "Status PM2.5 particulate matter (Hourly measured)",
        "PM10 particulate matter (Hourly measured)",
        "Nitrogen dioxide",
        "Ozone",
    ]
    assert find_measurement_column(columns, "pm25") == "PM2.5 particulate matter (Hourly measured)"
    assert find_measurement_column(columns, "pm10") == "PM10 particulate matter (Hourly measured)"
    assert find_measurement_column(columns, "no2") == "Nitrogen dioxide"
    assert find_measurement_column(columns, "o3") == "Ozone"


def test_parser_handles_real_preamble_status_and_html_pollutant_names():
    station = Station("CARD", "Cardiff Centre", "Urban Background", 51.48, -3.18)
    text = """Data supplied by UK-AIR on 1/5/2026
All Data GMT hour ending 
Status: R =Ratified P=Provisional,P*=As supplied
,,Cardiff Centre,,,,,,,,
Date,time,"PM<sub>10</sub> particulate matter (Hourly measured)",status,unit,"Nitrogen dioxide",status,unit,"Ozone",status,unit,"PM<sub>2.5</sub> particulate matter (Hourly measured)",status,unit
 
01-01-2025,01:00,11.594,R,ugm-3,15.0,R,ugm-3,75.3,R,ugm-3,4.000,P,ugm-3
"""
    parsed = parse_uk_air_csv(text, station)
    assert len(parsed) == 1
    assert parsed.loc[0, "pm25"] == 4.0
    assert parsed.loc[0, "pm10"] == 11.594
    assert parsed.loc[0, "no2"] == 15.0
    assert parsed.loc[0, "o3"] == 75.3
    assert parsed.loc[0, "pm25_status"] == "P"
    assert parsed.loc[0, "pm10_status"] == "R"


def test_parser_handles_hour_24_reporting_day():
    station = Station("TEST", "Test Site", "Urban Background", 51.5, -3.2)
    text = """Date,Time,PM2.5 particulate matter (Hourly measured),status,unit,PM10 particulate matter (Hourly measured),status,unit
11/08/2026,24:00,8.5,P,ugm-3,13.0,P,ugm-3
"""
    parsed = parse_uk_air_csv(text, station)
    assert parsed.loc[0, "timestamp"] == pd.Timestamp("2026-08-12T00:00:00Z")
    assert parsed.loc[0, "reporting_date"] == pd.Timestamp("2026-08-11T00:00:00Z")


def test_qc_flags_provisional_inconsistency_but_not_coherent_or_ratified_spike():
    hourly = pd.DataFrame(
        {
            "pm25": [430.0, 183.515, 150.0],
            "pm10": [16.425, 211.6, 30.0],
            "pm25_status": ["P", "P", "R"],
        }
    )
    screened = apply_pm25_qc(hourly)
    assert screened["pm25_qc_warning"].tolist() == [True, False, False]
    assert pd.isna(screened.loc[0, "pm25_screened"])
    assert screened.loc[1, "pm25_screened"] == 183.515
    assert screened.loc[2, "pm25_screened"] == 150.0


def test_daily_screened_mean_requires_18_valid_hours():
    timestamps = pd.date_range("2026-08-01", periods=24, freq="h", tz="UTC")
    hourly = pd.DataFrame(
        {
            "timestamp": timestamps,
            "reporting_date": pd.Timestamp("2026-08-01", tz="UTC"),
            "station_code": "A",
            "station_name": "Alpha",
            "site_type": "Urban Background",
            "latitude": 51.0,
            "longitude": -3.0,
            "pm25": [10.0] * 24,
            "pm25_screened": [10.0] * 17 + [None] * 7,
            "pm10": [20.0] * 24,
            "no2": [5.0] * 24,
            "o3": [30.0] * 24,
        }
    )
    daily = daily_means(hourly)
    assert daily.loc[0, "pm25"] == 10.0
    assert pd.isna(daily.loc[0, "pm25_screened"])
    assert daily.loc[0, "pm25_screened_hours"] == 17


def test_period_comparison_uses_screened_value_but_retains_raw_sensitivity():
    dates = pd.date_range("2026-01-01", periods=8, freq="D", tz="UTC")
    rows = []
    for date, raw, screened in zip(
        dates,
        [4, 4, 4, 4, 8, 8, 8, 100],
        [4, 4, 4, 4, 8, 8, 8, 8],
    ):
        rows.append(
            {
                "date": date,
                "station_code": "A",
                "station_name": "Alpha",
                "site_type": "Urban Background",
                "pm25": raw,
                "pm25_screened": screened,
            }
        )
    result = build_period_comparison(pd.DataFrame(rows), dates[4], dates[7], 4)
    assert result.loc[0, "recent_pm25_mean"] == 8.0
    assert result.loc[0, "pm25_change_pct"] == 100.0
    assert result.loc[0, "raw_recent_pm25_mean"] == 31.0


def test_site_relative_and_event_screen_require_peer_context():
    dates = pd.date_range("2026-01-01", periods=8, freq="D", tz="UTC")
    rows = []
    for date in dates:
        for index in range(5):
            rows.append(
                {
                    "date": date,
                    "station_code": str(index),
                    "station_name": str(index),
                    "site_type": "X",
                    "pm25": index + 1.0,
                    "pm25_screened": index + 1.0,
                    "pm10": 10 + index,
                    "no2": 2 + index,
                }
            )
    daily = pd.DataFrame(rows)
    relative = build_site_relative_daily(daily, min_peers=4)
    target = relative[(relative["date"] == dates[0]) & (relative["station_code"] == "4")].iloc[0]
    assert target["network_peer_count"] == 4
    assert target["network_median_excluding_station"] == 2.5
    assert target["site_relative_pm25"] == 2.5
    summary = build_site_relative_summary(relative, dates[4], dates[7], 4)
    assert len(summary) == 5
    event_screen = build_event_screen(daily, dates[4], dates[7], dates[0])
    assert len(event_screen) == 4
    assert (event_screen["sites_reporting"] == 5).all()


def _png_dimensions(path: Path):
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", data[16:24])


def test_dark_chart_suite_dimensions(tmp_path):
    stations = [
        Station("A", "Alpha", "Urban Background", 51.48, -3.18),
        Station("B", "Beta", "Rural Background", 51.78, -4.69),
        Station("C", "Gamma", "Urban Traffic", 52.0, -3.5),
        Station("D", "Delta", "Urban Industrial", 52.2, -3.2),
        Station("E", "Epsilon", "Urban Background", 52.5, -3.0),
    ]
    dates = pd.date_range("2026-07-01", periods=40, freq="D", tz="UTC")
    rows = []
    for day_index, date in enumerate(dates):
        for station_index, station in enumerate(stations):
            rows.append(
                {
                    "date": date,
                    "station_code": station.code,
                    "station_name": station.name,
                    "site_type": station.site_type,
                    "latitude": station.latitude,
                    "longitude": station.longitude,
                    "pm25": 5.0 + station_index + (day_index % 7),
                    "pm25_screened": 5.0 + station_index + (day_index % 7),
                    "pm10": 10.0 + station_index,
                    "no2": 8.0 + station_index,
                }
            )
    daily = pd.DataFrame(rows)
    latest, rolling_start, recent_start, _, _ = select_windows(daily, 30, 14)
    metadata = {
        "latest_observation_day_utc": latest.isoformat(),
        "rolling_start_utc": rolling_start.isoformat(),
        "recent_start_utc": recent_start.isoformat(),
        "rolling_days": 30,
        "recent_days": 14,
    }
    render_all_charts(daily, pd.DataFrame(), stations, metadata, tmp_path)

    stems = [
        "wales_aurn_pm25_rolling_year_dark",
        "wales_aurn_pm25_recent_dark",
        "wales_aurn_pm25_station_distribution_dark",
        "wales_aurn_pm25_recent_vs_previous_dark",
        "wales_aurn_pm25_site_relative_change_dark",
        "wales_aurn_pm25_july_event_screen_dark",
        "wales_aurn_pm25_station_map_dark",
    ]
    for stem in stems:
        assert _png_dimensions(tmp_path / f"{stem}.png") == (1600, 900)
        assert _png_dimensions(tmp_path / f"{stem}_square.png") == (1080, 1080)
        assert (tmp_path / f"{stem}.svg").exists()
        assert (tmp_path / f"{stem}_square.svg").exists()
