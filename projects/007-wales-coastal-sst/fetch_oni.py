"""Fetch NOAA CPC Oceanic Niño Index (ONI)."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

from constants import ONI_URL, RAW_DIR

# Fallback URLs if the primary CPC path moves.
ONI_URLS = (
    ONI_URL,
    "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt",
    "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/detrend.nino34.ascii.txt",
)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_oni(*, output_dir: Path = RAW_DIR) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_txt = output_dir / "oni.ascii.txt"
    last_err: Exception | None = None
    used_url = ONI_URLS[0]
    for url in ONI_URLS:
        try:
            print(f"Downloading ONI → {url}", flush=True)
            resp = requests.get(url, timeout=60)
            resp.raise_for_status()
            raw_txt.write_bytes(resp.content)
            used_url = url
            break
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            continue
    else:
        raise RuntimeError(f"Could not download ONI: {last_err}")

    df = pd.read_csv(raw_txt, sep=r"\s+")
    df.columns = [c.strip().upper() for c in df.columns]
    # Standard ONI ascii: SEAS YR TOTAL ANOM
    if "SEAS" not in df.columns and "SEASON" in df.columns:
        df = df.rename(columns={"SEASON": "SEAS"})
    if "YR" not in df.columns and "YEAR" in df.columns:
        df = df.rename(columns={"YEAR": "YR"})
    if "ANOM" not in df.columns and "ONI" in df.columns:
        df = df.rename(columns={"ONI": "ANOM"})

    season_mid_month = {
        "DJF": 1,
        "JFM": 2,
        "FMA": 3,
        "MAM": 4,
        "AMJ": 5,
        "MJJ": 6,
        "JJA": 7,
        "JAS": 8,
        "ASO": 9,
        "SON": 10,
        "OND": 11,
        "NDJ": 12,
    }
    df["month"] = df["SEAS"].map(season_mid_month)
    df = df.dropna(subset=["month"])
    df["date"] = pd.to_datetime(
        {"year": df["YR"].astype(int), "month": df["month"].astype(int), "day": 15},
        utc=True,
    )
    out_csv = output_dir / "oni.csv"
    export = pd.DataFrame(
        {
            "date": df["date"],
            "year": df["YR"].astype(int),
            "season": df["SEAS"].astype(str),
            "sst_nino34": pd.to_numeric(df.get("TOTAL", df.get("ANOM")), errors="coerce"),
            "oni": pd.to_numeric(df["ANOM"], errors="coerce"),
        }
    )
    export.to_csv(out_csv, index=False)

    provenance = {
        "product": "NOAA CPC Oceanic Niño Index (ONI)",
        "source_url": used_url,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "local_txt": raw_txt.name,
        "local_csv": out_csv.name,
        "bytes_txt": raw_txt.stat().st_size,
        "sha256_txt": _sha256(raw_txt),
        "row_count": int(len(export)),
        "note": "Pacific ENSO context only; not a Wales SST driver attribution.",
    }
    (output_dir / "oni.provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(f"  {len(export)} ONI rows · sha256 {provenance['sha256_txt'][:12]}…", flush=True)
    return provenance


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch NOAA ONI")
    parser.parse_args()
    print(json.dumps(fetch_oni(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
