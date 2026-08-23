"""Fetch Met Office HadISST monthly SST and extract a Wales-shelf subset."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from scipy.io import netcdf_file

from constants import (
    HADISST_TIME_ORIGIN,
    HADISST_URL,
    LAT_MAX,
    LAT_MIN,
    LON_MAX,
    LON_MIN,
    RAW_DIR,
)

LAND_FILL = -1.0e30


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_hadisst(*, output_dir: Path = RAW_DIR, keep_full: bool = False) -> dict:
    """Download HadISST, write Wales-shelf long CSV (+ optional full NetCDF)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    gz_path = output_dir / "HadISST_sst.nc.gz"
    print(f"Downloading HadISST → {gz_path.name}", flush=True)
    with requests.get(HADISST_URL, stream=True, timeout=600) as resp:
        resp.raise_for_status()
        with gz_path.open("wb") as fh:
            for chunk in resp.iter_content(chunk_size=1 << 20):
                if chunk:
                    fh.write(chunk)

    with tempfile.TemporaryDirectory() as tmp:
        nc_path = Path(tmp) / "HadISST_sst.nc"
        with gzip.open(gz_path, "rb") as src, nc_path.open("wb") as dst:
            shutil.copyfileobj(src, dst)
        if keep_full:
            shutil.copy2(nc_path, output_dir / "HadISST_sst.nc")

        ds = netcdf_file(str(nc_path), "r", mmap=False)
        time = np.asarray(ds.variables["time"][:], dtype=float)
        lat = np.asarray(ds.variables["latitude"][:], dtype=float)
        lon = np.asarray(ds.variables["longitude"][:], dtype=float)
        dates = pd.to_datetime(HADISST_TIME_ORIGIN) + pd.to_timedelta(time, unit="D")
        dates = pd.DatetimeIndex(dates).tz_localize("UTC")

        lat_i = np.where((lat >= LAT_MIN) & (lat <= LAT_MAX))[0]
        lon_i = np.where((lon >= LON_MIN) & (lon <= LON_MAX))[0]
        sst = np.asarray(ds.variables["sst"][:, lat_i][:, :, lon_i], dtype=float)
        sst = np.where(sst < -1.0e5, np.nan, sst)
        ds.close()

        rows = []
        for t_idx, date in enumerate(dates):
            for yi, y in enumerate(lat_i):
                for xi, x in enumerate(lon_i):
                    val = sst[t_idx, yi, xi]
                    if np.isnan(val):
                        continue
                    rows.append(
                        {
                            "date": date.isoformat(),
                            "latitude": float(lat[y]),
                            "longitude": float(lon[x]),
                            "sst_c": float(val),
                        }
                    )
        out_csv = output_dir / "hadisst_wales_shelf_monthly.csv"
        pd.DataFrame(rows).to_csv(out_csv, index=False, float_format="%.4f")

    provenance = {
        "product": "Met Office HadISST1 monthly SST",
        "source_url": HADISST_URL,
        "bbox": {"lon_min": LON_MIN, "lon_max": LON_MAX, "lat_min": LAT_MIN, "lat_max": LAT_MAX},
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "local_gz": gz_path.name,
        "local_csv": out_csv.name,
        "bytes_gz": gz_path.stat().st_size,
        "sha256_gz": _sha256(gz_path),
        "sha256_csv": _sha256(out_csv),
        "n_rows": int(len(rows)),
        "note": "Stage A uses HadISST monthly (open HadOBS). Daily NOAA OISST remains a higher-resolution follow-on.",
    }
    (output_dir / "hadisst_wales_shelf.provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(f"  Wales CSV {out_csv.name}: {len(rows)} rows · gz sha256 {provenance['sha256_gz'][:12]}…", flush=True)
    return provenance


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch HadISST Wales shelf subset")
    parser.add_argument("--keep-full", action="store_true", help="Also retain full NetCDF")
    args = parser.parse_args()
    print(json.dumps(fetch_hadisst(keep_full=args.keep_full), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
