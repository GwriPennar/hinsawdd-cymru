from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build import SOURCES, cluster_detections, fetch_firms_csv, parse_and_normalize, summarize_incidents

SWANSEA_GOWER_BBOX = (-4.35, 51.52, -3.85, 51.72)


def _inside_bbox(frame: pd.DataFrame, bbox: tuple[float, float, float, float]) -> pd.Series:
    west, south, east, north = bbox
    return frame["longitude"].between(west, east) & frame["latitude"].between(south, north)


def filter_recent(
    detections: pd.DataFrame,
    *,
    bbox: tuple[float, float, float, float],
    hours: float,
    now: datetime | None = None,
) -> pd.DataFrame:
    if hours <= 0:
        raise ValueError("hours must be positive")
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    cutoff = now.astimezone(timezone.utc) - timedelta(hours=hours)
    return detections[_inside_bbox(detections, bbox) & (detections["acq_datetime_utc"] >= cutoff)].copy()


def _api_days(hours: float) -> int:
    return max(1, min(5, math.ceil(hours / 24)))


def run_local_watch(
    *,
    map_key: str,
    output_root: Path,
    bbox: tuple[float, float, float, float] = SWANSEA_GOWER_BBOX,
    hours: float = 5,
    now: datetime | None = None,
) -> dict:
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    output_root = Path(output_root)
    derived = output_root / "data" / "derived"
    raw = output_root / "data" / "raw" / now.strftime("%Y%m%dT%H%M%SZ")
    derived.mkdir(parents=True, exist_ok=True)
    raw.mkdir(parents=True, exist_ok=False)

    frames: list[pd.DataFrame] = []
    source_errors: dict[str, str] = {}
    manifests: list[dict] = []

    with requests.Session() as session:
        session.headers.update({"User-Agent": "hinsawdd-cymru-swansea-gower-watch/0.1"})
        for source in SOURCES:
            try:
                payload, safe_endpoint = fetch_firms_csv(
                    session,
                    map_key,
                    source,
                    bbox,
                    _api_days(hours),
                )
                (raw / f"{source}.csv").write_bytes(payload)
                frames.append(parse_and_normalize(payload, source))
                manifests.append({"source": source, "endpoint": safe_endpoint, "bytes": len(payload)})
            except Exception as exc:
                source_errors[source] = f"{type(exc).__name__}: {exc}"

    if not frames:
        raise RuntimeError("All NASA FIRMS sources failed; no local watch data could be produced")

    detections = pd.concat(frames, ignore_index=True)
    recent = filter_recent(detections, bbox=bbox, hours=hours, now=now)
    clustered = cluster_detections(recent)
    incidents = summarize_incidents(clustered)

    out_detections = recent.copy()
    out_clustered = clustered.copy()
    out_incidents = incidents.copy()
    for frame in (out_detections, out_clustered):
        if "acq_datetime_utc" in frame:
            frame["acq_datetime_utc"] = frame["acq_datetime_utc"].map(lambda v: v.isoformat())
    for col in ("first_detected_utc", "last_detected_utc"):
        if col in out_incidents:
            out_incidents[col] = out_incidents[col].map(lambda v: v.isoformat() if hasattr(v, "isoformat") else v)

    out_detections.to_csv(derived / "detections.csv", index=False)
    out_clustered.to_csv(derived / "clustered_detections.csv", index=False)
    out_incidents.to_csv(derived / "incidents.csv", index=False)

    summary = {
        "area": "Swansea and Gower",
        "bbox": list(bbox),
        "window_hours": hours,
        "generated_at_utc": now.isoformat(),
        "cutoff_utc": (now - timedelta(hours=hours)).isoformat(),
        "detection_count": int(len(recent)),
        "incident_count": int(len(incidents)),
        "latest_detection_utc": recent["acq_datetime_utc"].max().isoformat() if len(recent) else None,
        "successful_sources": sorted(recent["source"].astype(str).unique().tolist()) if len(recent) else sorted({m["source"] for m in manifests}),
        "source_errors": source_errors,
        "partial_source_data": bool(source_errors),
        "status": "satellite thermal anomalies; not confirmed wildfire incidents",
        "raw_snapshot_dir": str(raw.relative_to(output_root)),
        "input_manifests": manifests,
    }
    (derived / "summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Data-only recent FIRMS watch for Swansea and Gower")
    parser.add_argument("--hours", type=float, default=5)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "published" / "local" / "swansea-gower",
    )
    args = parser.parse_args(argv)

    key = os.getenv("NASA_FIRMS_MAP_KEY", "").strip()
    if not key:
        parser.error("NASA_FIRMS_MAP_KEY is required")

    summary = run_local_watch(map_key=key, output_root=args.output_root, hours=args.hours)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
