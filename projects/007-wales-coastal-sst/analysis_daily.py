"""Derive daily ODYSSEA Wales-shelf series, DOY climatology and anomaly fields."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from constants import (
    DERIVED_DIR,
    LAT_MAX,
    LAT_MIN,
    LON_MAX,
    LON_MIN,
    ODYSSEA_CLIM_END,
    ODYSSEA_CLIM_START,
    RAW_DIR,
)


def _ocean_sst_c(ds: xr.Dataset) -> xr.DataArray:
    return ds["analysed_sst"].where(ds["mask"] == 1) - 273.15


def _month_day_key(index: pd.DatetimeIndex) -> pd.Index:
    return pd.Index([f"{ts.month:02d}-{ts.day:02d}" for ts in index])


def analyse_daily(
    *,
    daily_path: Path | None = None,
    yearly_dir: Path | None = None,
    latest_nc: Path | None = None,
    oni_path: Path | None = None,
    output_dir: Path = DERIVED_DIR,
    clim_start: int = ODYSSEA_CLIM_START,
    clim_end: int = ODYSSEA_CLIM_END,
) -> dict:
    daily_path = daily_path or (RAW_DIR / "odyssea_wales_shelf_daily_mean.csv")
    yearly_dir = yearly_dir or (RAW_DIR / "odyssea_yearly")
    latest_nc = latest_nc or (RAW_DIR / "odyssea_wales_latest.nc")
    oni_path = oni_path or (RAW_DIR / "oni.csv")
    output_dir.mkdir(parents=True, exist_ok=True)

    header = pd.read_csv(daily_path, nrows=0)
    date_col = "date" if "date" in header.columns else header.columns[0]
    frame = pd.read_csv(daily_path, parse_dates=[date_col])
    if "sst_c" not in frame.columns:
        raise ValueError(f"Expected sst_c in {daily_path}")
    frame[date_col] = pd.to_datetime(frame[date_col], utc=True)
    frame = frame.set_index(date_col).sort_index()
    frame.index.name = "date"

    frame["md"] = _month_day_key(frame.index)
    clim_mask = (frame.index.year >= clim_start) & (frame.index.year <= clim_end)
    clim = frame.loc[clim_mask].groupby("md")["sst_c"].mean()
    frame["clim_sst_c"] = frame["md"].map(clim)
    frame["anomaly_c"] = frame["sst_c"] - frame["clim_sst_c"]
    out_series = frame[["sst_c", "clim_sst_c", "anomaly_c"]].dropna(subset=["clim_sst_c"])
    series_csv = output_dir / "wales_shelf_sst_daily.csv"
    out_series.to_csv(series_csv, float_format="%.4f")

    latest = xr.open_dataset(latest_nc)
    latest_sst = _ocean_sst_c(latest).isel(time=0)
    latest_date = pd.Timestamp(latest.time.values[0], tz="UTC")
    md = f"{latest_date.month:02d}-{latest_date.day:02d}"
    clim_stacks = []
    for year in range(clim_start, clim_end + 1):
        path = yearly_dir / f"odyssea_wales_{year}.nc"
        if not path.exists():
            continue
        ds = xr.open_dataset(path)
        times = pd.to_datetime(ds.time.values, utc=True)
        hits = np.where(_month_day_key(pd.DatetimeIndex(times)) == md)[0]
        if len(hits) == 0:
            ds.close()
            continue
        clim_stacks.append(_ocean_sst_c(ds).isel(time=int(hits[0])))
        ds.close()
    if not clim_stacks:
        raise FileNotFoundError(f"No clim-year grids found for {md} under {yearly_dir}")
    clim_grid = xr.concat(clim_stacks, dim="year").mean("year")
    anomaly = latest_sst - clim_grid
    lat, lon = np.meshgrid(anomaly["latitude"].values, anomaly["longitude"].values, indexing="ij")
    anom_df = pd.DataFrame(
        {
            "latitude": lat.ravel(),
            "longitude": lon.ravel(),
            "sst_c": latest_sst.values.ravel(),
            "clim_sst": clim_grid.values.ravel(),
            "anomaly_c": anomaly.values.ravel(),
        }
    ).dropna(subset=["anomaly_c"])
    anom_csv = output_dir / "wales_shelf_sst_daily_anomaly_grid_latest.csv"
    anom_df.to_csv(anom_csv, index=False, float_format="%.4f")
    latest.close()

    oni = pd.read_csv(oni_path, parse_dates=["date"])
    if getattr(oni["date"].dt, "tz", None) is None:
        oni["date"] = oni["date"].dt.tz_localize("UTC")

    recent = out_series.tail(30)
    summary = {
        "project": "007-wales-coastal-sst",
        "stage": "B",
        "product": "Copernicus Marine ODYSSEA L4 daily (~0.02°)",
        "bbox": {"lon_min": LON_MIN, "lon_max": LON_MAX, "lat_min": LAT_MIN, "lat_max": LAT_MAX},
        "climatology": f"{clim_start}-{clim_end} day-of-year (ODYSSEA)",
        "series_start": out_series.index.min().isoformat(),
        "series_end": out_series.index.max().isoformat(),
        "n_days": int(len(out_series)),
        "latest_date": latest_date.date().isoformat(),
        "latest_sst_c": round(float(out_series["sst_c"].iloc[-1]), 3),
        "latest_anomaly_c": round(float(out_series["anomaly_c"].iloc[-1]), 3),
        "mean_anomaly_last_30d_c": round(float(recent["anomaly_c"].mean()), 3),
        "mean_sst_last_30d_c": round(float(recent["sst_c"].mean()), 3),
        "latest_oni_season": str(oni.iloc[-1]["season"]),
        "latest_oni_year": int(oni.iloc[-1]["year"]),
        "latest_oni": float(oni.iloc[-1]["oni"]),
        "outputs": {
            "daily_csv": series_csv.name,
            "anomaly_grid_csv": anom_csv.name,
        },
        "caveat": (
            "Wales-shelf area-mean from ODYSSEA L4 foundation SST (daily analysis). "
            f"Anomalies use {clim_start}–{clim_end} ODYSSEA day-of-year normals (not 1991–2020). "
            "ONI is Pacific ENSO context only — not Wales causation."
        ),
    }
    (output_dir / "summary_daily.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main() -> int:
    print(json.dumps(analyse_daily(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
