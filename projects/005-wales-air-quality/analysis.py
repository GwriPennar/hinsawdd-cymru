#!/usr/bin/env python3
"""Project 005: Wales air-quality baseline and cautious event-screen analysis."""
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
MIN_NETWORK_PEERS = 4
QC_PM25_ABSOLUTE = 100.0
QC_PM25_TO_PM10_RATIO = 2.0

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
            str(row.code),
            str(row.name),
            str(row.site_type),
            float(row.latitude),
            float(row.longitude),
        )
        for row in df.itertuples(index=False)
    ]


def _normalise_column(value: str) -> str:
    text = str(value).strip().lower().replace("₂", "2").replace("₁₀", "10")
    text = re.sub(r"<\s*/?\s*sub\s*>", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text)


def _table_text(text: str) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        first_two = [part.strip().strip('"').lower() for part in line.split(",", 2)[:2]]
        if first_two == ["date", "time"]:
            return "\n".join(lines[index:])
    raise ValueError("UK-AIR table header 'Date,time' not found")


def find_measurement_column(columns: Iterable[str], pollutant: str) -> str | None:
    aliases = POLLUTANT_ALIASES[pollutant]
    candidates: list[tuple[int, int, str]] = []
    for col in columns:
        norm = _normalise_column(col)
        if any(token in norm for token in STATUS_TOKENS):
            continue
        for rank, alias in enumerate(aliases):
            if norm == alias or alias in norm:
                candidates.append((rank, len(str(col)), col))
                break
    return sorted(candidates)[0][2] if candidates else None


def find_status_column(columns: Iterable[str], measurement_col: str | None) -> str | None:
    if measurement_col is None:
        return None
    cols = list(columns)
    index = cols.index(measurement_col)
    if index + 1 < len(cols) and _normalise_column(cols[index + 1]).startswith("status"):
        return cols[index + 1]
    return None


def _find_column(columns: Iterable[str], exact: str) -> str:
    for col in columns:
        if _normalise_column(col) == exact:
            return col
    raise ValueError(f"Required column {exact!r} not found")


def parse_uk_air_csv(text: str, station: Station) -> pd.DataFrame:
    raw = pd.read_csv(StringIO(_table_text(text)))
    date_col = _find_column(raw.columns, "date")
    time_col = _find_column(raw.columns, "time")
    dates = pd.to_datetime(
        raw[date_col].astype(str).str.strip(), dayfirst=True, errors="coerce"
    )
    times = raw[time_col].astype(str).str.strip()
    deltas = pd.to_timedelta(
        times.where(times.str.count(":").eq(2), times + ":00"), errors="coerce"
    )
    out = pd.DataFrame(
        {
            "timestamp": (dates + deltas).dt.tz_localize("UTC"),
            "reporting_date": dates.dt.tz_localize("UTC"),
        }
    )
    for pollutant in POLLUTANT_ALIASES:
        source = find_measurement_column(raw.columns, pollutant)
        status = find_status_column(raw.columns, source)
        out[pollutant] = pd.to_numeric(raw[source], errors="coerce") if source else pd.NA
        out[f"{pollutant}_status"] = (
            raw[status].astype("string").str.strip() if status else pd.NA
        )
    out["station_code"] = station.code
    out["station_name"] = station.name
    out["site_type"] = station.site_type
    out["latitude"] = station.latitude
    out["longitude"] = station.longitude
    return out.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)


def apply_pm25_qc(hourly: pd.DataFrame) -> pd.DataFrame:
    """Add a conservative sensitivity flag; raw observations are never overwritten."""
    out = hourly.copy()
    pm25 = pd.to_numeric(out["pm25"], errors="coerce")
    pm10 = pd.to_numeric(out["pm10"], errors="coerce")
    status = (
        out.get("pm25_status", pd.Series(pd.NA, index=out.index))
        .astype("string")
        .str.upper()
        .fillna("")
    )
    provisional = status.str.startswith("P")
    internally_inconsistent = (
        pm25.ge(QC_PM25_ABSOLUTE)
        & pm10.notna()
        & pm10.ge(0)
        & pm25.gt(QC_PM25_TO_PM10_RATIO * pm10)
    )
    out["pm25_qc_warning"] = provisional & internally_inconsistent
    out["pm25_qc_reason"] = ""
    out.loc[out["pm25_qc_warning"], "pm25_qc_reason"] = (
        "provisional PM2.5 >=100 and >2x collocated PM10; review before event attribution"
    )
    out["pm25_screened"] = pm25.mask(out["pm25_qc_warning"])
    return out


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
    manifest = {
        "site_code": station.code,
        "year": year,
        "url": url,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "sha256": hashlib.sha256(response.content).hexdigest(),
        "bytes": len(response.content),
        "status": "provisional or ratified according to upstream record",
    }
    (raw_dir / f"{station.code}_{year}.provenance.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return parse_uk_air_csv(response.text, station)


def download_observations(
    stations: list[Station], years: Iterable[int], raw_dir: Path
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    with requests.Session() as session:
        session.headers.update({"User-Agent": "hinsawdd-cymru-project-005/0.2"})
        for station in stations:
            for year in years:
                frames.append(fetch_site_year(session, station, year, raw_dir))
    if not frames:
        raise ValueError("No observations downloaded")
    return pd.concat(frames, ignore_index=True).sort_values(["station_code", "timestamp"])


def load_retained_observations(
    stations: list[Station], years: Iterable[int], raw_dir: Path
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for station in stations:
        for year in years:
            path = raw_dir / f"{station.code}_{year}.csv"
            if not path.exists():
                raise FileNotFoundError(path)
            frames.append(
                parse_uk_air_csv(
                    path.read_text(encoding="utf-8", errors="replace"), station
                )
            )
    return pd.concat(frames, ignore_index=True).sort_values(["station_code", "timestamp"])


def daily_means(
    hourly: pd.DataFrame, min_hourly: int = MIN_HOURLY_VALUES_PER_DAY
) -> pd.DataFrame:
    working = hourly.copy()
    if "pm25_screened" not in working:
        working["pm25_screened"] = pd.to_numeric(working["pm25"], errors="coerce")
    working["date"] = pd.to_datetime(
        working.get("reporting_date", working["timestamp"]), utc=True
    ).dt.floor("D")
    id_cols = [
        "station_code",
        "station_name",
        "site_type",
        "latitude",
        "longitude",
        "date",
    ]
    measures = ["pm25", "pm25_screened", "pm10", "no2", "o3"]
    pieces: list[pd.DataFrame] = []
    for measure in measures:
        grouped = working.groupby(id_cols, dropna=False)[measure]
        piece = pd.concat(
            [
                grouped.mean().rename(measure),
                grouped.count().rename(f"{measure}_hours"),
            ],
            axis=1,
        ).reset_index()
        piece.loc[piece[f"{measure}_hours"] < min_hourly, measure] = pd.NA
        pieces.append(piece)
    daily = pieces[0]
    for piece in pieces[1:]:
        daily = daily.merge(piece, on=id_cols, how="outer")
    return daily.sort_values(["date", "station_code"]).reset_index(drop=True)


def build_summary(
    daily: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp
) -> pd.DataFrame:
    subset = daily[daily["date"].between(start, end)].copy()
    expected = max(1, (end.normalize() - start.normalize()).days + 1)
    rows = []
    for (code, name, site_type), group in subset.groupby(
        ["station_code", "station_name", "site_type"], dropna=False
    ):
        raw = pd.to_numeric(group["pm25"], errors="coerce").dropna()
        screened = pd.to_numeric(group["pm25_screened"], errors="coerce").dropna()
        rows.append(
            {
                "station_code": code,
                "station_name": name,
                "site_type": site_type,
                "valid_pm25_days": len(screened),
                "expected_days": expected,
                "pm25_daily_coverage_pct": round(100 * len(screened) / expected, 1),
                "pm25_daily_mean": screened.mean() if len(screened) else None,
                "pm25_daily_median": screened.median() if len(screened) else None,
                "pm25_daily_p95": screened.quantile(0.95) if len(screened) else None,
                "pm25_daily_max": screened.max() if len(screened) else None,
                "pm25_daily_mean_raw": raw.mean() if len(raw) else None,
                "pm25_daily_max_raw": raw.max() if len(raw) else None,
            }
        )
    return pd.DataFrame(rows).sort_values("station_name").reset_index(drop=True)


def build_period_comparison(
    daily: pd.DataFrame,
    recent_start: pd.Timestamp,
    end: pd.Timestamp,
    period_days: int,
) -> pd.DataFrame:
    previous_start = recent_start - pd.Timedelta(days=period_days)
    previous_end = recent_start - pd.Timedelta(days=1)
    id_cols = ["station_code", "station_name", "site_type"]
    measure = "pm25_screened" if "pm25_screened" in daily else "pm25"

    def summary(start: pd.Timestamp, stop: pd.Timestamp, prefix: str, col: str):
        out = (
            daily[daily["date"].between(start, stop)]
            .groupby(id_cols, dropna=False)[col]
            .agg(["count", "mean"])
            .reset_index()
        )
        return out.rename(
            columns={"count": f"{prefix}_valid_days", "mean": f"{prefix}_pm25_mean"}
        )

    previous = summary(previous_start, previous_end, "previous", measure)
    recent = summary(recent_start, end, "recent", measure)
    result = previous.merge(recent, on=id_cols, how="outer")
    for prefix in ("previous", "recent"):
        result[f"{prefix}_coverage_pct"] = (
            100 * result[f"{prefix}_valid_days"] / period_days
        ).round(1)
    result["pm25_change"] = result["recent_pm25_mean"] - result["previous_pm25_mean"]
    result["pm25_change_pct"] = (
        100 * result["pm25_change"] / result["previous_pm25_mean"]
    ).round(1)
    if measure != "pm25":
        raw_previous = summary(previous_start, previous_end, "raw_previous", "pm25").drop(
            columns=["raw_previous_valid_days"]
        )
        raw_recent = summary(recent_start, end, "raw_recent", "pm25").drop(
            columns=["raw_recent_valid_days"]
        )
        result = result.merge(raw_previous, on=id_cols, how="left").merge(
            raw_recent, on=id_cols, how="left"
        )
        result["raw_pm25_change_pct"] = (
            100
            * (result["raw_recent_pm25_mean"] - result["raw_previous_pm25_mean"])
            / result["raw_previous_pm25_mean"]
        ).round(1)
    result["previous_start_utc"] = previous_start.isoformat()
    result["previous_end_utc"] = previous_end.isoformat()
    result["recent_start_utc"] = recent_start.isoformat()
    result["recent_end_utc"] = end.isoformat()
    return result.sort_values("station_name").reset_index(drop=True)


def build_site_relative_daily(
    daily: pd.DataFrame, min_peers: int = MIN_NETWORK_PEERS
) -> pd.DataFrame:
    value_col = "pm25_screened" if "pm25_screened" in daily else "pm25"
    rows = []
    for date, group in daily.groupby("date"):
        values = pd.to_numeric(group[value_col], errors="coerce")
        for index, row in group.iterrows():
            value = pd.to_numeric(pd.Series([row[value_col]]), errors="coerce").iloc[0]
            peers = values[(group.index != index) & values.notna()]
            median = float(peers.median()) if len(peers) >= min_peers else None
            rows.append(
                {
                    "date": date,
                    "station_code": row.station_code,
                    "station_name": row.station_name,
                    "site_type": row.site_type,
                    "pm25_screened": value,
                    "pm10": row.get("pm10"),
                    "no2": row.get("no2"),
                    "network_peer_count": int(len(peers)),
                    "network_median_excluding_station": median,
                    "site_relative_pm25": (
                        float(value) - median
                        if pd.notna(value) and median is not None
                        else None
                    ),
                }
            )
    return pd.DataFrame(rows).sort_values(["date", "station_name"]).reset_index(drop=True)


def _corr(group: pd.DataFrame, left: str, right: str) -> float | None:
    pair = group[[left, right]].apply(pd.to_numeric, errors="coerce").dropna()
    if len(pair) < 3 or pair[left].nunique() < 2 or pair[right].nunique() < 2:
        return None
    return float(pair[left].corr(pair[right]))


def build_site_relative_summary(
    site_daily: pd.DataFrame,
    recent_start: pd.Timestamp,
    end: pd.Timestamp,
    period_days: int,
) -> pd.DataFrame:
    previous_start = recent_start - pd.Timedelta(days=period_days)
    previous_end = recent_start - pd.Timedelta(days=1)
    id_cols = ["station_code", "station_name", "site_type"]

    def summarise(start: pd.Timestamp, stop: pd.Timestamp, prefix: str):
        rows = []
        window = site_daily[site_daily["date"].between(start, stop)]
        for key, group in window.groupby(id_cols, dropna=False):
            valid = group.dropna(
                subset=[
                    "pm25_screened",
                    "network_median_excluding_station",
                    "site_relative_pm25",
                ]
            )
            rows.append(
                dict(zip(id_cols, key))
                | {
                    f"{prefix}_valid_days": len(valid),
                    f"{prefix}_pm25_mean": valid["pm25_screened"].mean() if len(valid) else None,
                    f"{prefix}_network_median_mean": valid["network_median_excluding_station"].mean() if len(valid) else None,
                    f"{prefix}_site_relative_mean": valid["site_relative_pm25"].mean() if len(valid) else None,
                    f"{prefix}_network_corr": _corr(valid, "pm25_screened", "network_median_excluding_station"),
                    f"{prefix}_no2_corr": _corr(valid, "pm25_screened", "no2"),
                    f"{prefix}_pm10_corr": _corr(valid, "pm25_screened", "pm10"),
                }
            )
        return pd.DataFrame(rows)

    result = summarise(previous_start, previous_end, "previous").merge(
        summarise(recent_start, end, "recent"), on=id_cols, how="outer"
    )
    result["site_relative_change"] = (
        result["recent_site_relative_mean"] - result["previous_site_relative_mean"]
    )
    result["previous_start_utc"] = previous_start.isoformat()
    result["previous_end_utc"] = previous_end.isoformat()
    result["recent_start_utc"] = recent_start.isoformat()
    result["recent_end_utc"] = end.isoformat()
    return result.sort_values("station_name").reset_index(drop=True)


def build_event_screen(
    daily: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    baseline_start: pd.Timestamp,
) -> pd.DataFrame:
    value_col = "pm25_screened" if "pm25_screened" in daily else "pm25"
    baseline = daily[daily["date"].between(baseline_start, end)]
    p90 = baseline.groupby("station_code")[value_col].quantile(0.90).to_dict()
    rows = []
    for date, group in daily[daily["date"].between(start, end)].groupby("date"):
        values = pd.to_numeric(group[value_col], errors="coerce")
        valid = group[values.notna()].copy()
        valid[value_col] = values[values.notna()]
        if valid.empty:
            continue
        max_row = valid.loc[valid[value_col].idxmax()]
        above = sum(
            float(row[value_col]) > p90.get(row.station_code, float("inf"))
            for _, row in valid.iterrows()
        )
        rows.append(
            {
                "date": date,
                "sites_reporting": len(valid),
                "network_median_pm25": float(valid[value_col].median()),
                "network_mean_pm25": float(valid[value_col].mean()),
                "max_station": max_row.station_name,
                "max_pm25": float(max_row[value_col]),
                "stations_above_rolling_p90": int(above),
            }
        )
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


def build_hourly_event_candidates(
    hourly: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp
) -> pd.DataFrame:
    working = hourly[hourly["timestamp"].between(start, end)].copy()
    pm25 = pd.to_numeric(working["pm25_screened"], errors="coerce")
    pm10 = pd.to_numeric(working["pm10"], errors="coerce")
    mask = pm25.ge(50) & pm10.notna() & (pm25 / pm10).between(0.5, 1.5)
    cols = [
        "timestamp",
        "station_code",
        "station_name",
        "site_type",
        "pm25_screened",
        "pm10",
        "no2",
        "pm25_status",
        "pm10_status",
    ]
    out = working.loc[mask, cols].copy()
    out["pm25_to_pm10_ratio"] = out["pm25_screened"] / out["pm10"]
    return out.sort_values("timestamp").reset_index(drop=True)


def select_windows(daily: pd.DataFrame, rolling_days: int, recent_days: int):
    latest = pd.Timestamp(daily["date"].max())
    rolling_start = latest - pd.Timedelta(days=rolling_days - 1)
    recent_start = latest - pd.Timedelta(days=recent_days - 1)
    return (
        latest,
        rolling_start,
        recent_start,
        daily[daily["date"].between(rolling_start, latest)].copy(),
        daily[daily["date"].between(recent_start, latest)].copy(),
    )


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
    build_summary(daily, rolling_start, latest).to_csv(
        derived_dir / "pm25_station_summary.csv", index=False
    )
    build_period_comparison(daily, recent_start, latest, recent_days).to_csv(
        derived_dir / "pm25_recent_vs_previous.csv", index=False
    )

    qc = hourly[hourly["pm25_qc_warning"]].copy()
    qc_cols = [
        "timestamp",
        "reporting_date",
        "station_code",
        "station_name",
        "pm25",
        "pm25_status",
        "pm10",
        "pm10_status",
        "pm25_qc_reason",
    ]
    qc[qc_cols].to_csv(derived_dir / "pm25_qc_warnings.csv", index=False)

    site_daily = build_site_relative_daily(daily)
    site_daily.to_csv(derived_dir / "pm25_site_relative_daily.csv", index=False)
    build_site_relative_summary(site_daily, recent_start, latest, recent_days).to_csv(
        derived_dir / "pm25_site_relative_change.csv", index=False
    )

    event_screen = build_event_screen(daily, recent_start, latest, rolling_start)
    event_screen.to_csv(derived_dir / "pm25_event_screen.csv", index=False)
    event_screen.sort_values(
        ["network_median_pm25", "sites_reporting"], ascending=[False, False]
    ).head(15).to_csv(derived_dir / "pm25_event_screen_top15.csv", index=False)

    july_start = pd.Timestamp("2026-07-13", tz="UTC")
    july_end = min(latest, pd.Timestamp("2026-07-24", tz="UTC"))
    build_hourly_event_candidates(
        hourly,
        july_start,
        july_end + pd.Timedelta(days=1) - pd.Timedelta(seconds=1),
    ).to_csv(derived_dir / "pm25_july_hourly_event_candidates.csv", index=False)

    metadata = {
        "latest_observation_day_utc": latest.isoformat(),
        "rolling_start_utc": rolling_start.isoformat(),
        "recent_start_utc": recent_start.isoformat(),
        "rolling_days": rolling_days,
        "recent_days": recent_days,
        "daily_minimum_hourly_capture": MIN_HOURLY_VALUES_PER_DAY,
        "pm25_station_count_with_valid_daily_data": int(
            rolling.groupby("station_code")["pm25_screened"].count().gt(0).sum()
        ),
        "pm25_qc_warning_count": int(qc.shape[0]),
        "qc_rule": (
            "screen sensitivity only: provisional PM2.5 >=100 and >2x collocated PM10; raw retained"
        ),
        "scientific_boundary": (
            "Observational decomposition only. QC sensitivity and site-relative residuals are not "
            "source apportionment or wildfire attribution."
        ),
    }
    (derived_dir / "summary.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    project_dir = Path(__file__).resolve().parent
    parser.add_argument(
        "--stations", type=Path, default=project_dir / "data" / "stations.csv"
    )
    parser.add_argument("--raw-dir", type=Path, default=project_dir / "data" / "raw")
    parser.add_argument(
        "--derived-dir", type=Path, default=project_dir / "data" / "derived"
    )
    parser.add_argument("--figures-dir", type=Path, default=project_dir / "figures")
    parser.add_argument("--rolling-days", type=int, default=DEFAULT_ROLLING_DAYS)
    parser.add_argument("--recent-days", type=int, default=DEFAULT_RECENT_DAYS)
    parser.add_argument(
        "--use-retained",
        action="store_true",
        help="Parse already-retained annual source files instead of downloading",
    )
    args = parser.parse_args()

    stations = load_stations(args.stations)
    now = datetime.now(timezone.utc)
    years = range(now.year - 1, now.year + 1)
    loader = load_retained_observations if args.use_retained else download_observations
    hourly = loader(stations, years, args.raw_dir)
    hourly = apply_pm25_qc(hourly)
    daily = daily_means(hourly)
    metadata = write_outputs(
        hourly, daily, args.derived_dir, args.rolling_days, args.recent_days
    )

    from charts import render_all_charts

    render_all_charts(daily, hourly, stations, metadata, args.figures_dir)
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
