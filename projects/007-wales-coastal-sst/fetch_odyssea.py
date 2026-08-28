"""Fetch Copernicus ODYSSEA L4 daily SST for the Wales shelf box."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from constants import (
    LAT_MAX,
    LAT_MIN,
    LON_MAX,
    LON_MIN,
    ODYSSEA_CLIM_END,
    ODYSSEA_CLIM_START,
    ODYSSEA_DATASET_ID,
    ODYSSEA_PRODUCT_ID,
    RAW_DIR,
    REGION_LAT_MAX,
    REGION_LAT_MIN,
    REGION_LON_MAX,
    REGION_LON_MIN,
)

try:
    import copernicusmarine as cm
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Install Stage B deps: pip install -e '.[sst]'") from exc


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _ocean_sst_c(ds: xr.Dataset) -> xr.DataArray:
    return ds["analysed_sst"].where(ds["mask"] == 1) - 273.15


def _area_mean_c(sst_c: xr.DataArray) -> pd.Series:
    weights = np.cos(np.deg2rad(sst_c["latitude"]))
    mean = sst_c.weighted(weights).mean(dim=("latitude", "longitude"), skipna=True)
    series = mean.to_series()
    series.index = pd.to_datetime(series.index, utc=True)
    series.name = "sst_c"
    return series


def fetch_region_snapshot(*, output_dir: Path = RAW_DIR, end_ts: pd.Timestamp | None = None) -> dict:
    """Download latest-day + DOY climatology grids for the NW Europe snapshot bbox."""
    output_dir.mkdir(parents=True, exist_ok=True)
    if end_ts is None:
        probe = cm.open_dataset(
            dataset_id=ODYSSEA_DATASET_ID,
            variables=["analysed_sst"],
            minimum_longitude=REGION_LON_MIN,
            maximum_longitude=REGION_LON_MIN + 0.05,
            minimum_latitude=REGION_LAT_MIN,
            maximum_latitude=REGION_LAT_MIN + 0.05,
        )
        end_ts = pd.Timestamp(probe.time.values[-1], tz="UTC")
        probe.close()

    latest_nc = output_dir / "odyssea_region_latest.nc"
    print(f"ODYSSEA region latest day → {latest_nc.name}", flush=True)
    if latest_nc.exists():
        latest_nc.unlink()
    cm.subset(
        dataset_id=ODYSSEA_DATASET_ID,
        variables=["analysed_sst", "mask"],
        minimum_longitude=REGION_LON_MIN,
        maximum_longitude=REGION_LON_MAX,
        minimum_latitude=REGION_LAT_MIN,
        maximum_latitude=REGION_LAT_MAX,
        start_datetime=end_ts.strftime("%Y-%m-%dT00:00:00"),
        end_datetime=end_ts.strftime("%Y-%m-%dT00:00:00"),
        output_filename=latest_nc.name,
        output_directory=str(output_dir),
    )

    md = f"{end_ts.month:02d}-{end_ts.day:02d}"
    clim_nc = output_dir / "odyssea_region_clim.nc"
    print(f"ODYSSEA region clim DOY {md} → {clim_nc.name}", flush=True)
    if clim_nc.exists():
        clim_nc.unlink()
    clim_stacks: list[xr.DataArray] = []
    for year in range(ODYSSEA_CLIM_START, ODYSSEA_CLIM_END + 1):
        day = pd.Timestamp(f"{year}-{md}", tz="UTC")
        tmp = output_dir / f"_odyssea_region_clim_{year}.nc"
        if tmp.exists():
            tmp.unlink()
        cm.subset(
            dataset_id=ODYSSEA_DATASET_ID,
            variables=["analysed_sst", "mask"],
            minimum_longitude=REGION_LON_MIN,
            maximum_longitude=REGION_LON_MAX,
            minimum_latitude=REGION_LAT_MIN,
            maximum_latitude=REGION_LAT_MAX,
            start_datetime=day.strftime("%Y-%m-%dT00:00:00"),
            end_datetime=day.strftime("%Y-%m-%dT00:00:00"),
            output_filename=tmp.name,
            output_directory=str(output_dir),
        )
        with xr.open_dataset(tmp) as ds:
            clim_stacks.append(_ocean_sst_c(ds).isel(time=0))
        tmp.unlink(missing_ok=True)
    clim_grid = xr.concat(clim_stacks, dim="year").mean("year")
    xr.Dataset({"sst_c": clim_grid}).to_netcdf(clim_nc)

    meta = {
        "bbox": {
            "lon_min": REGION_LON_MIN,
            "lon_max": REGION_LON_MAX,
            "lat_min": REGION_LAT_MIN,
            "lat_max": REGION_LAT_MAX,
        },
        "latest_date": end_ts.date().isoformat(),
        "clim_doy": md,
        "local_latest_nc": latest_nc.name,
        "local_clim_nc": clim_nc.name,
        "sha256_latest_nc": _sha256(latest_nc),
        "sha256_clim_nc": _sha256(clim_nc),
    }
    (output_dir / "odyssea_region.provenance.json").write_text(json.dumps(meta, indent=2) + "\n")
    return meta


def fetch_odyssea(
    *,
    output_dir: Path = RAW_DIR,
    start: str | None = None,
    end: str | None = None,
) -> dict:
    """Download Wales-box ODYSSEA, write daily means + yearly NetCDFs + provenance."""
    output_dir.mkdir(parents=True, exist_ok=True)
    yearly_dir = output_dir / "odyssea_yearly"
    yearly_dir.mkdir(parents=True, exist_ok=True)

    probe = cm.open_dataset(
        dataset_id=ODYSSEA_DATASET_ID,
        variables=["analysed_sst"],
        minimum_longitude=LON_MIN,
        maximum_longitude=LON_MIN + 0.05,
        minimum_latitude=LAT_MIN,
        maximum_latitude=LAT_MIN + 0.05,
    )
    t0 = pd.Timestamp(probe.time.values[0], tz="UTC")
    t1 = pd.Timestamp(probe.time.values[-1], tz="UTC")
    probe.close()
    start_ts = pd.Timestamp(start or t0.date().isoformat(), tz="UTC")
    end_ts = pd.Timestamp(end or t1.date().isoformat(), tz="UTC")

    frames: list[pd.Series] = []
    year_files: list[str] = []
    for year in range(start_ts.year, end_ts.year + 1):
        y0 = max(start_ts, pd.Timestamp(f"{year}-01-01", tz="UTC"))
        y1 = min(end_ts, pd.Timestamp(f"{year}-12-31", tz="UTC"))
        out_nc = yearly_dir / f"odyssea_wales_{year}.nc"
        print(f"ODYSSEA subset {y0.date()} → {y1.date()} → {out_nc.name}", flush=True)
        if out_nc.exists():
            out_nc.unlink()
        cm.subset(
            dataset_id=ODYSSEA_DATASET_ID,
            variables=["analysed_sst", "mask"],
            minimum_longitude=LON_MIN,
            maximum_longitude=LON_MAX,
            minimum_latitude=LAT_MIN,
            maximum_latitude=LAT_MAX,
            start_datetime=y0.strftime("%Y-%m-%dT00:00:00"),
            end_datetime=y1.strftime("%Y-%m-%dT00:00:00"),
            output_filename=out_nc.name,
            output_directory=str(yearly_dir),
        )
        ds = xr.open_dataset(out_nc)
        frames.append(_area_mean_c(_ocean_sst_c(ds)))
        ds.close()
        year_files.append(out_nc.name)

    daily = pd.concat(frames).sort_index()
    daily = daily[~daily.index.duplicated(keep="last")]
    daily.index.name = "date"
    daily_csv = output_dir / "odyssea_wales_shelf_daily_mean.csv"
    daily.to_frame().to_csv(daily_csv, float_format="%.4f")

    latest_nc = output_dir / "odyssea_wales_latest.nc"
    print(f"ODYSSEA latest day → {latest_nc.name}", flush=True)
    if latest_nc.exists():
        latest_nc.unlink()
    cm.subset(
        dataset_id=ODYSSEA_DATASET_ID,
        variables=["analysed_sst", "mask"],
        minimum_longitude=LON_MIN,
        maximum_longitude=LON_MAX,
        minimum_latitude=LAT_MIN,
        maximum_latitude=LAT_MAX,
        start_datetime=end_ts.strftime("%Y-%m-%dT00:00:00"),
        end_datetime=end_ts.strftime("%Y-%m-%dT00:00:00"),
        output_filename=latest_nc.name,
        output_directory=str(output_dir),
    )

    provenance = {
        "product": "Copernicus Marine ODYSSEA NW Shelf / IBI L4 SST (NRT)",
        "product_id": ODYSSEA_PRODUCT_ID,
        "dataset_id": ODYSSEA_DATASET_ID,
        "bbox": {"lon_min": LON_MIN, "lon_max": LON_MAX, "lat_min": LAT_MIN, "lat_max": LAT_MAX},
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "start": start_ts.date().isoformat(),
        "end": end_ts.date().isoformat(),
        "n_days": int(len(daily)),
        "local_daily_csv": daily_csv.name,
        "local_latest_nc": latest_nc.name,
        "local_yearly_dir": yearly_dir.name,
        "yearly_files": year_files,
        "sha256_daily_csv": _sha256(daily_csv),
        "sha256_latest_nc": _sha256(latest_nc),
        "note": "Yearly NetCDF extracts are local/cache only; derived daily CSV is retained in git.",
    }
    (output_dir / "odyssea_wales_shelf.provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(f"  daily means: {len(daily)} days · sha256 {provenance['sha256_daily_csv'][:12]}…", flush=True)
    provenance["region_snapshot"] = fetch_region_snapshot(output_dir=output_dir, end_ts=end_ts)
    return provenance


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch ODYSSEA Wales shelf daily SST")
    parser.add_argument("--start", default=None, help="YYYY-MM-DD (default: dataset start)")
    parser.add_argument("--end", default=None, help="YYYY-MM-DD (default: dataset end)")
    args = parser.parse_args()
    print(json.dumps(fetch_odyssea(start=args.start, end=args.end), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
