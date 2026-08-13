"""Historical and cumulative NASA FIRMS data for Project 006.

Backfill mode retrieves the requested number of days in FIRMS Area API chunks
(maximum five days/request) for the coarse Wales query box and retains every raw
CSV response with SHA-256 provenance. Append mode folds the latest daily live
run into the cumulative detection table without deleting earlier observations.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent


def _load_build():
    spec = importlib.util.spec_from_file_location("project006_build", ROOT / "build.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _history_paths(history_root: Path):
    return history_root / "detections.csv", history_root / "daily_summary.csv"


def _normalise_for_storage(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    if "acq_datetime_utc" in out:
        out["acq_datetime_utc"] = pd.to_datetime(out["acq_datetime_utc"], utc=True, errors="coerce")
        out = out.dropna(subset=["acq_datetime_utc"])
        out["acq_datetime_utc"] = out["acq_datetime_utc"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return out


def _dedupe(frame: pd.DataFrame) -> pd.DataFrame:
    keys = ["source", "satellite", "acq_datetime_utc", "latitude", "longitude"]
    existing = [key for key in keys if key in frame.columns]
    out = frame.drop_duplicates(existing) if existing else frame.drop_duplicates()
    return out.sort_values(["acq_datetime_utc", "latitude", "longitude", "source"]).reset_index(drop=True)


def _write_summary(frame: pd.DataFrame, history_root: Path) -> None:
    work = frame.copy()
    work["acq_datetime_utc"] = pd.to_datetime(work["acq_datetime_utc"], utc=True, errors="coerce")
    work = work.dropna(subset=["acq_datetime_utc"])
    work["date_utc"] = work["acq_datetime_utc"].dt.strftime("%Y-%m-%d")
    summary = (
        work.groupby("date_utc", as_index=False)
        .agg(
            detection_count=("latitude", "size"),
            satellite_count=("satellite", "nunique"),
            source_count=("source", "nunique"),
            peak_frp_mw=("frp", "max"),
        )
        .sort_values("date_utc")
    )
    summary.to_csv(history_root / "daily_summary.csv", index=False)


def append_detections(history_root: Path, incoming_path: Path) -> dict:
    history_root.mkdir(parents=True, exist_ok=True)
    history_path, _ = _history_paths(history_root)
    incoming = pd.read_csv(incoming_path)
    if "in_wales_watch_bbox" in incoming.columns:
        mask = incoming["in_wales_watch_bbox"].astype(str).str.lower().isin({"true", "1"})
        incoming = incoming[mask].copy()
    if history_path.exists():
        previous = pd.read_csv(history_path)
        combined = pd.concat([previous, incoming], ignore_index=True, sort=False)
    else:
        combined = incoming
    combined = _dedupe(_normalise_for_storage(combined))
    combined.to_csv(history_path, index=False)
    _write_summary(combined, history_root)
    manifest = {
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "append",
        "detection_count": int(len(combined)),
        "earliest_utc": combined["acq_datetime_utc"].min() if len(combined) else None,
        "latest_utc": combined["acq_datetime_utc"].max() if len(combined) else None,
        "note": "Cumulative coarse-Wales query record; thermal anomalies are not confirmed wildfires.",
    }
    (history_root / "history_manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def backfill(history_root: Path, days: int, end_date: date | None = None) -> dict:
    if days < 1:
        raise ValueError("days must be positive")
    build = _load_build()
    map_key = os.getenv("NASA_FIRMS_MAP_KEY", "").strip()
    if not map_key:
        raise RuntimeError("NASA_FIRMS_MAP_KEY is required for historical backfill")

    end = end_date or datetime.now(timezone.utc).date()
    start = end - timedelta(days=days - 1)
    raw_root = history_root / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    frames = []
    requests_manifest = []

    with requests.Session() as session:
        session.headers.update({"User-Agent": "hinsawdd-cymru-wildfire-watch-history/0.1"})
        cursor = start
        while cursor <= end:
            chunk_days = min(5, (end - cursor).days + 1)
            chunk_end = cursor + timedelta(days=chunk_days - 1)
            chunk_dir = raw_root / f"{cursor.isoformat()}_{chunk_end.isoformat()}"
            chunk_dir.mkdir(parents=True, exist_ok=True)
            for source in build.SOURCES:
                last_error = None
                for attempt in range(3):
                    try:
                        payload, safe = build.fetch_firms_csv(
                            session, map_key, source, build.WALES_WATCH_BBOX, chunk_days, cursor.isoformat(), timeout=90
                        )
                        break
                    except RuntimeError as exc:
                        last_error = exc
                        if attempt == 2:
                            raise
                        time.sleep(2 ** attempt)
                path = chunk_dir / f"{source}.csv"
                path.write_bytes(payload)
                frame = build.parse_and_normalize(payload, source)
                frames.append(frame)
                requests_manifest.append({
                    "source": source,
                    "start_date": cursor.isoformat(),
                    "end_date": chunk_end.isoformat(),
                    "safe_endpoint": safe,
                    "raw_path": str(path.relative_to(history_root)),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "bytes": len(payload),
                    "row_count": int(len(frame)),
                })
            cursor = chunk_end + timedelta(days=1)

    detections = pd.concat(frames, ignore_index=True, sort=False) if frames else pd.DataFrame()
    detections = _dedupe(_normalise_for_storage(detections)) if len(detections) else detections
    history_root.mkdir(parents=True, exist_ok=True)
    detections.to_csv(history_root / "detections.csv", index=False)
    if len(detections):
        _write_summary(detections, history_root)
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "historical_backfill",
        "requested_start_date": start.isoformat(),
        "requested_end_date": end.isoformat(),
        "requested_days": days,
        "query_bbox": list(build.WALES_WATCH_BBOX),
        "query_bbox_note": "Coarse retrieval box; exact official Wales filtering is a downstream spatial step.",
        "sources": list(build.SOURCES),
        "detection_count": int(len(detections)),
        "requests": requests_manifest,
        "evidence_note": "FIRMS thermal anomalies are observations, not confirmed wildfire incidents.",
    }
    (history_root / "history_manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Backfill or append Project 006 FIRMS history")
    parser.add_argument("--history-root", type=Path, default=ROOT / "data" / "history")
    parser.add_argument("--days", type=int, default=60)
    parser.add_argument("--end-date", type=lambda value: date.fromisoformat(value))
    parser.add_argument("--append-detections", type=Path)
    args = parser.parse_args(argv)
    if args.append_detections:
        result = append_detections(args.history_root, args.append_detections)
    else:
        result = backfill(args.history_root, args.days, args.end_date)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
