#!/usr/bin/env python3
"""Project 005: reference-grade Wales air-quality baseline from DEFRA UK-AIR AURN."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests

BASE_URL = "https://uk-air.defra.gov.uk/datastore/data_files/site_data/{site}_{year}.csv?v=1"
DEFAULT_ROLLING_DAYS = 365
DEFAULT_RECENT_DAYS = 70
MIN_HOURLY_VALUES_PER_DAY = 18

POLLUTANT_ALIASES = {
    "pm25": (
        "pm2.5 particulate matter (hourly measured)",
        "particulates < 2.5um (hourly measured)",
        "pm2.5",
        "pm25",
    ),
    "pm10": (
        "pm10 particulate matter (hourly measured)",
        "particulates < 10um (hourly measured)",
        "pm10",
        "ge10",
    ),
    "no2": ("nitrogen dioxide", "no2"),
    "o3": ("ozone", "o3"),
}

STATUS_TOKENS = ("status", "unit", "units", "flag")


@dataclass(frozen=True)
class Station:
    code: str
    name: str
    site_type: str
    latitude: float
    longitude: float


def load_stations(path: Path) -> list[Station]:
    df = pd.read_csv(path)
    required = {"code", "name", "site_type", "latitude", "longitude"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Station metadata missing columns: {sorted(missing)}")
    return [
        Station(
            code=str(row.code),
            name=str(row.name),
            site_type=str(row.site_type),
            latitude=float(row.latitude),
            longitude=float(row.longitude),
        )
        for row in df.itertuples(index=False)
    ]


def _normalise_column(value: str) -> str:
    text = str(value).strip().lower()
    text = text.replace("₂", "2").replace("₁₀", "10")
    text = re.sub(r"<\s*sub\s*>", "", text)
    text = re.sub(r"<\s*/\s*sub\s*>", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _table_text(text: str) -> str:
    """Return the tabular portion of a UK-AIR annual site CSV.

    UK-AIR annual files include descriptive preamble rows before the real
    Date,time header. Locate the header by content rather than assuming a
    fixed row count so the parser remains robust to preamble changes.
    """
    lines = text.splitlines()
    for index, line in enumerate(lines):
        first_two = [part.strip().strip('"').lower() for part in line.split(',', 2)[:2]]
        if first_two == ["date", "time"]:
            return "\n".join(lines[index:])
    raise ValueError("UK-AIR table header 'Date,time' not found")


def find_measurement_column(columns: Iterable[str], pollutant: str) -> str | None:
    aliases = POLLUTANT_ALIASES[pollutant]
    normalised = {col: _normalise_column(col) for col in columns}
    candidates: list[tuple[int, str]] = []
    for col, norm in normalised.items():
        if any(token in norm for token in STATUS_TOKENS):
            continue
        for rank, alias in enumerate(aliases):
            if norm == alias or alias in norm:
                candidates.append((rank, col))
                break
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], len(item[1])))
    return candidates[0][1]


def _find_column(columns: Iterable[str], exact: str) -> str:
    for col in columns:
        if _normalise_column(col) == exact:
            return col
    raise ValueError(f"Required column {exact!r} not found")


def parse_uk_air_csv(text: str, station: Station) -> pd.DataFrame:
    raw = pd.read_csv(StringIO(_table_text(text)))
    date_col = _find_column(raw.columns, "date")
    time_col = _find_column(raw.columns, "time")

    date_values = pd.to_datetime(
        raw[date_col].astype(str).str.strip(),
        dayfirst=True,
        errors="coerce",
    )
    time_text = raw[time_col].astype(str).str.strip()
    time_delta = pd.to_timedelta(
        time_text.where(time_text.str.count(":").eq(2), time_text + ":00"),
        errors="coerce",
    )
    timestamp = (date_values + time_delta).dt.tz_localize("UTC")
    reporting_date = date_values.dt.tz_localize("UTC")
    out = pd.DataFrame({"timestamp": timestamp, "reporting_date": reporting_date})
    for pollutant in POLLUTANT_ALIASES:
        source = find_measurement_column(raw.columns, pollutant)
        if source is not None:
            out[pollutant] = pd.to_numeric(raw[source], errors="coerce")
        else:
            out[pollutant] = pd.NA

    out["station_code"] = station.code
    out["station_name"] = station.name
    out["site_type"] = station.site_type
    out["latitude"] = station.latitude
    out["longitude"] = station.longitude
    return out.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)


def fetch_site_year(
    session: requests.Session,
    station: Station,
    year: int,
    raw_dir: Path,
    timeout: int = 60,
) -> pd.DataFrame:
    url = BASE_URL.format(site=station.code, year=year)
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    raw_dir.mkdir(parents=True, exist_ok=True)
    target = raw_dir / f"{station.code}_{year}.csv"
    target.write_bytes(response.content)
    digest = hashlib.sha256(response.content).hexdigest()
    (raw_dir / f"{station.code}_{year}.provenance.json").write_text(
        json.dumps(
            {
                "site_code": station.code,
                "year": year,
                "url": url,
                "retrieved_utc": datetime.now(timezone.utc).isoformat(),
                "sha256": digest,
                "bytes": len(response.content),
                "status": "provisional or ratified according to upstream record",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return parse_uk_air_csv(response.text, station)


def download_observations(
    stations: list[Station],
    years: Iterable[int],
    raw_dir: Path,
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    with requests.Session() as session:
        session.headers.update({"User-Agent": "hinsawdd-cymru-project-005/0.1"})
        for station in stations:
            for year in years:
                frames.append(fetch_site_year(session, station, year, raw_dir))
    if not frames:
        raise ValueError("No observations downloaded")
    return pd.concat(frames, ignore_index=True).sort_values(["station_code", "timestamp"])


def daily_means(
    hourly: pd.DataFrame,
    min_hourly: int = MIN_HOURLY_VALUES_PER_DAY,
) -> pd.DataFrame:
    working = hourly.copy()
    if "reporting_date" in working.columns:
        working["date"] = pd.to_datetime(working["reporting_date"], utc=True).dt.floor("D")
    else:
        working["date"] = working["timestamp"].dt.floor("D")
    id_cols = ["station_code", "station_name", "site_type", "latitude", "longitude", "date"]
    rows: list[pd.DataFrame] = []
    for pollutant in POLLUTANT_ALIASES:
        grouped = working.groupby(id_cols, dropna=False)[pollutant]
        mean = grouped.mean().rename(pollutant)
        count = grouped.count().rename(f"{pollutant}_hours")
        piece = pd.concat([mean, count], axis=1).reset_index()
        piece.loc[piece[f"{pollutant}_hours"] < min_hourly, pollutant] = pd.NA
        rows.append(piece)

    daily = rows[0]
    for piece in rows[1:]:
        keep = id_cols + [c for c in piece.columns if c not in id_cols]
        daily = daily.merge(piece[keep], on=id_cols, how="outer")
    return daily.sort_values(["date", "station_code"]).reset_index(drop=True)


def build_summary(daily: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    subset = daily[(daily["date"] >= start) & (daily["date"] <= end)].copy()
    expected_days = max(1, (end.normalize() - start.normalize()).days + 1)
    rows = []
    for (code, name, site_type), group in subset.groupby(
        ["station_code", "station_name", "site_type"], dropna=False
    ):
        valid = pd.to_numeric(group["pm25"], errors="coerce").dropna()
        rows.append(
            {
                "station_code": code,
                "station_name": name,
                "site_type": site_type,
                "valid_pm25_days": int(valid.shape[0]),
                "expected_days": expected_days,
                "pm25_daily_coverage_pct": round(100 * valid.shape[0] / expected_days, 1),
                "pm25_daily_mean": float(valid.mean()) if len(valid) else None,
                "pm25_daily_median": float(valid.median()) if len(valid) else None,
                "pm25_daily_p95": float(valid.quantile(0.95)) if len(valid) else None,
                "pm25_daily_max": float(valid.max()) if len(valid) else None,
            }
        )
    return pd.DataFrame(rows).sort_values("station_name").reset_index(drop=True)


def select_windows(daily: pd.DataFrame, rolling_days: int, recent_days: int):
    latest = pd.Timestamp(daily["date"].max())
    rolling_start = latest - pd.Timedelta(days=rolling_days - 1)
    recent_start = latest - pd.Timedelta(days=recent_days - 1)
    rolling = daily[daily["date"].between(rolling_start, latest)].copy()
    recent = daily[daily["date"].between(recent_start, latest)].copy()
    return latest, rolling_start, recent_start, rolling, recent


def write_outputs(
    hourly: pd.DataFrame,
    daily: pd.DataFrame,
    derived_dir: Path,
    rolling_days: int,
    recent_days: int,
) -> dict:
    derived_dir.mkdir(parents=True, exist_ok=True)
    latest, rolling_start, recent_start, rolling, recent = select_windows(
        daily, rolling_days, recent_days
    )
    hourly.to_csv(derived_dir / "aurn_hourly_combined.csv", index=False)
    daily.to_csv(derived_dir / "aurn_daily_means.csv", index=False)
    rolling.to_csv(derived_dir / "pm25_rolling_year_daily.csv", index=False)
    recent.to_csv(derived_dir / "pm25_recent_daily.csv", index=False)
    summary = build_summary(daily, rolling_start, latest)
    summary.to_csv(derived_dir / "pm25_station_summary.csv", index=False)

    metadata = {
        "latest_observation_day_utc": latest.isoformat(),
        "rolling_start_utc": rolling_start.isoformat(),
        "recent_start_utc": recent_start.isoformat(),
        "rolling_days": rolling_days,
        "recent_days": recent_days,
        "daily_minimum_hourly_capture": MIN_HOURLY_VALUES_PER_DAY,
        "pm25_station_count_with_valid_daily_data": int(
            rolling.groupby("station_code")["pm25"].count().gt(0).sum()
        ),
        "scientific_boundary": (
            "Observational baseline only. No wildfire, traffic, industrial or meteorological "
            "attribution is made by this stage."
        ),
    }
    (derived_dir / "summary.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    project_dir = Path(__file__).resolve().parent
    parser.add_argument("--stations", type=Path, default=project_dir / "data" / "stations.csv")
    parser.add_argument("--raw-dir", type=Path, default=project_dir / "data" / "raw")
    parser.add_argument("--derived-dir", type=Path, default=project_dir / "data" / "derived")
    parser.add_argument("--figures-dir", type=Path, default=project_dir / "figures")
    parser.add_argument("--rolling-days", type=int, default=DEFAULT_ROLLING_DAYS)
    parser.add_argument("--recent-days", type=int, default=DEFAULT_RECENT_DAYS)
    args = parser.parse_args()

    stations = load_stations(args.stations)
    now = datetime.now(timezone.utc)
    years = range(now.year - 1, now.year + 1)
    hourly = download_observations(stations, years, args.raw_dir)
    daily = daily_means(hourly)
    metadata = write_outputs(hourly, daily, args.derived_dir, args.rolling_days, args.recent_days)

    from charts import render_all_charts

    render_all_charts(daily, stations, metadata, args.figures_dir)
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
