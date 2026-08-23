"""Derive Wales-shelf monthly SST series, climatology and anomaly fields."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from constants import CLIM_END, CLIM_START, DERIVED_DIR, LAT_MAX, LAT_MIN, LON_MAX, LON_MIN, RAW_DIR


def ocean_mean_from_lat_sst(lat: np.ndarray, sst: np.ndarray) -> float:
    w = np.cos(np.deg2rad(lat.astype(float)))
    mask = ~np.isnan(sst.astype(float))
    return float(np.sum(sst[mask] * w[mask]) / np.sum(w[mask]))


def analyse(
    *,
    hadisst_path: Path | None = None,
    oni_path: Path | None = None,
    output_dir: Path = DERIVED_DIR,
) -> dict:
    hadisst_path = hadisst_path or (RAW_DIR / "hadisst_wales_shelf_monthly.csv")
    oni_path = oni_path or (RAW_DIR / "oni.csv")
    output_dir.mkdir(parents=True, exist_ok=True)

    grid = pd.read_csv(hadisst_path)
    grid["date"] = pd.to_datetime(grid["date"], utc=True, format="mixed")
    grid["month_start"] = pd.to_datetime(grid["date"].dt.strftime("%Y-%m-01"), utc=True)

    rows = []
    for month_start, chunk in grid.groupby("month_start", sort=True):
        rows.append(
            {
                "date": month_start,
                "sst_c": ocean_mean_from_lat_sst(chunk["latitude"].to_numpy(), chunk["sst_c"].to_numpy()),
            }
        )
    frame = pd.DataFrame(rows).set_index("date").sort_index()
    frame["month"] = frame.index.month
    clim_mask = (frame.index.year >= CLIM_START) & (frame.index.year <= CLIM_END)
    clim = frame.loc[clim_mask].groupby("month")["sst_c"].mean()
    frame["clim_sst_c"] = frame["month"].map(lambda m: float(clim.loc[int(m)]))
    frame["anomaly_c"] = frame["sst_c"] - frame["clim_sst_c"]
    frame = frame.drop(columns=["month"])
    frame.index.name = "date"
    series_csv = output_dir / "wales_shelf_sst_monthly.csv"
    frame.to_csv(series_csv, float_format="%.4f")

    latest_month = grid["month_start"].max()
    day = grid.loc[grid["month_start"] == latest_month].copy()
    month = int(pd.Timestamp(latest_month).month)
    clim_cells = grid.loc[
        (grid["date"].dt.year >= CLIM_START)
        & (grid["date"].dt.year <= CLIM_END)
        & (grid["date"].dt.month == month)
    ]
    clim_grid = (
        clim_cells.groupby(["latitude", "longitude"], as_index=False)["sst_c"]
        .mean()
        .rename(columns={"sst_c": "clim_sst"})
    )
    merged = day.merge(clim_grid, on=["latitude", "longitude"], how="left")
    merged["anomaly_c"] = merged["sst_c"] - merged["clim_sst"]
    anom_csv = output_dir / "wales_shelf_sst_anomaly_grid_latest.csv"
    merged[["latitude", "longitude", "anomaly_c", "sst_c", "clim_sst"]].dropna(subset=["anomaly_c"]).to_csv(
        anom_csv, index=False, float_format="%.4f"
    )

    oni = pd.read_csv(oni_path, parse_dates=["date"])
    if getattr(oni["date"].dt, "tz", None) is None:
        oni["date"] = oni["date"].dt.tz_localize("UTC")

    recent = frame.tail(12)
    summary = {
        "project": "007-wales-coastal-sst",
        "stage": "A",
        "product": "Met Office HadISST1 monthly",
        "bbox": {"lon_min": LON_MIN, "lon_max": LON_MAX, "lat_min": LAT_MIN, "lat_max": LAT_MAX},
        "climatology": f"{CLIM_START}-{CLIM_END}",
        "series_start": frame.index.min().isoformat(),
        "series_end": frame.index.max().isoformat(),
        "n_months": int(len(frame)),
        "latest_date": frame.index.max().date().isoformat(),
        "latest_sst_c": round(float(frame["sst_c"].iloc[-1]), 3),
        "latest_anomaly_c": round(float(frame["anomaly_c"].iloc[-1]), 3),
        "mean_anomaly_last_12m_c": round(float(recent["anomaly_c"].mean()), 3),
        "mean_sst_last_12m_c": round(float(recent["sst_c"].mean()), 3),
        "latest_oni_season": str(oni.iloc[-1]["season"]),
        "latest_oni_year": int(oni.iloc[-1]["year"]),
        "latest_oni": float(oni.iloc[-1]["oni"]),
        "outputs": {"monthly_csv": series_csv.name, "anomaly_grid_csv": anom_csv.name},
        "caveat": (
            "Wales-shelf area-mean from Met Office HadISST1 (monthly, 1°). "
            "ONI is Pacific ENSO context only — not Wales causation."
        ),
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main() -> int:
    print(json.dumps(analyse(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
