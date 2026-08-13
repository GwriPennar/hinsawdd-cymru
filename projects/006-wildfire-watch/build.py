from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests

PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT_ROOT = PROJECT_DIR
FIRMS_AREA_API = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
VIIRS_SOURCES = (
    "VIIRS_SNPP_NRT",
    "VIIRS_NOAA20_NRT",
    "VIIRS_NOAA21_NRT",
)
UK_BBOX = (-8.8, 49.7, 2.0, 61.0)
# A rectangular watch window used only for MVP emphasis. It is deliberately
# not labelled as the national boundary and may include small neighbouring areas.
WALES_WATCH_BBOX = (-5.6, 51.2, -2.55, 53.5)
REQUIRED_COLUMNS = {
    "latitude",
    "longitude",
    "acq_date",
    "acq_time",
    "satellite",
    "instrument",
    "confidence",
    "version",
    "frp",
    "daynight",
}
CONFIDENCE_LABELS = {"l": "low", "n": "nominal", "h": "high"}
CONFIDENCE_RANK = {"low": 0, "nominal": 1, "high": 2}


def _bbox_text(bbox: tuple[float, float, float, float]) -> str:
    return ",".join(f"{value:g}" for value in bbox)


def _inside_bbox(lat: float, lon: float, bbox: tuple[float, float, float, float]) -> bool:
    west, south, east, north = bbox
    return west <= lon <= east and south <= lat <= north


def _safe_endpoint(source: str, bbox: tuple[float, float, float, float], days: int, date: str | None) -> str:
    endpoint = f"{FIRMS_AREA_API}/{{MAP_KEY}}/{source}/{_bbox_text(bbox)}/{days}"
    if date:
        endpoint += f"/{date}"
    return endpoint


def fetch_firms_csv(
    session: requests.Session,
    map_key: str,
    source: str,
    bbox: tuple[float, float, float, float],
    days: int,
    date: str | None = None,
    timeout: int = 60,
) -> tuple[bytes, str]:
    if source not in VIIRS_SOURCES:
        raise ValueError(f"Unsupported source: {source}")
    if not 1 <= days <= 5:
        raise ValueError("NASA FIRMS Area API day range must be between 1 and 5")

    url = f"{FIRMS_AREA_API}/{map_key}/{source}/{_bbox_text(bbox)}/{days}"
    if date:
        url += f"/{date}"
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    payload = response.content
    if not payload.strip():
        raise RuntimeError(f"NASA FIRMS returned an empty response for {source}")
    return payload, _safe_endpoint(source, bbox, days, date)


def parse_and_normalize(payload: bytes, source: str) -> pd.DataFrame:
    try:
        raw = pd.read_csv(io.BytesIO(payload))
    except Exception as exc:  # pandas raises several parser exceptions
        raise ValueError(f"Could not parse FIRMS CSV for {source}: {exc}") from exc

    missing = REQUIRED_COLUMNS - set(raw.columns)
    if missing:
        raise ValueError(f"FIRMS CSV for {source} is missing columns: {sorted(missing)}")

    frame = raw.copy()
    for column in ("latitude", "longitude", "frp"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    time_text = frame["acq_time"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(4)
    frame["acq_datetime_utc"] = pd.to_datetime(
        frame["acq_date"].astype(str) + " " + time_text,
        format="%Y-%m-%d %H%M",
        errors="coerce",
        utc=True,
    )
    frame["confidence_label"] = (
        frame["confidence"].astype(str).str.strip().str.lower().map(CONFIDENCE_LABELS).fillna("unknown")
    )
    frame["source"] = source
    frame["in_wales_watch_bbox"] = [
        _inside_bbox(lat, lon, WALES_WATCH_BBOX)
        if math.isfinite(lat) and math.isfinite(lon)
        else False
        for lat, lon in zip(frame["latitude"], frame["longitude"])
    ]

    frame = frame.dropna(subset=["latitude", "longitude", "acq_datetime_utc"]).copy()
    frame = frame[
        frame["latitude"].between(-90, 90) & frame["longitude"].between(-180, 180)
    ].copy()

    keep = [
        "latitude",
        "longitude",
        "acq_datetime_utc",
        "acq_date",
        "acq_time",
        "satellite",
        "instrument",
        "confidence",
        "confidence_label",
        "version",
        "frp",
        "daynight",
        "source",
        "in_wales_watch_bbox",
    ]
    for optional in ("bright_ti4", "bright_ti5", "scan", "track"):
        if optional in frame.columns:
            keep.append(optional)

    frame = frame[keep].copy()
    frame = frame.sort_values(["acq_datetime_utc", "latitude", "longitude", "source"]).reset_index(drop=True)
    frame = frame.drop_duplicates(
        subset=["source", "satellite", "acq_datetime_utc", "latitude", "longitude"],
        keep="first",
    ).reset_index(drop=True)
    return frame


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0088
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * radius_km * math.asin(min(1.0, math.sqrt(a)))


def cluster_detections(
    detections: pd.DataFrame,
    distance_km: float = 5.0,
    time_hours: float = 18.0,
) -> pd.DataFrame:
    if detections.empty:
        return detections.assign(cluster_id=pd.Series(dtype="int64"))
    if distance_km <= 0 or time_hours <= 0:
        raise ValueError("Cluster distance and time must be positive")

    work = detections.sort_values("acq_datetime_utc").reset_index(drop=True).copy()
    n = len(work)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    times = work["acq_datetime_utc"].tolist()
    lats = work["latitude"].astype(float).tolist()
    lons = work["longitude"].astype(float).tolist()
    max_seconds = time_hours * 3600

    for i in range(n):
        for j in range(i + 1, n):
            delta_seconds = (times[j] - times[i]).total_seconds()
            if delta_seconds > max_seconds:
                break
            if haversine_km(lats[i], lons[i], lats[j], lons[j]) <= distance_km:
                union(i, j)

    roots = [find(i) for i in range(n)]
    root_to_cluster = {root: idx + 1 for idx, root in enumerate(dict.fromkeys(roots))}
    work["cluster_id"] = [root_to_cluster[root] for root in roots]
    return work


def _incident_id(group: pd.DataFrame) -> str:
    first = group.sort_values(["acq_datetime_utc", "latitude", "longitude", "source"]).iloc[0]
    seed = (
        f"{first['acq_datetime_utc'].isoformat()}|"
        f"{float(first['latitude']):.5f}|{float(first['longitude']):.5f}|{first['source']}"
    )
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:7].upper()
    return f"HC-TA-{first['acq_datetime_utc']:%Y%m%d}-{digest}"


def summarize_incidents(clustered: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "incident_id",
        "latitude",
        "longitude",
        "detection_count",
        "satellite_count",
        "satellites",
        "sources",
        "first_detected_utc",
        "last_detected_utc",
        "duration_hours",
        "peak_frp_mw",
        "mean_frp_mw",
        "max_confidence",
        "daynight",
        "in_wales_watch_bbox",
    ]
    if clustered.empty:
        return pd.DataFrame(columns=columns)

    records: list[dict[str, object]] = []
    for _, group in clustered.groupby("cluster_id", sort=True):
        first_time = group["acq_datetime_utc"].min()
        last_time = group["acq_datetime_utc"].max()
        confidence_values = [value for value in group["confidence_label"].astype(str) if value in CONFIDENCE_RANK]
        max_confidence = max(confidence_values, key=lambda value: CONFIDENCE_RANK[value]) if confidence_values else "unknown"
        frp = pd.to_numeric(group["frp"], errors="coerce")
        records.append(
            {
                "incident_id": _incident_id(group),
                "latitude": round(float(group["latitude"].mean()), 5),
                "longitude": round(float(group["longitude"].mean()), 5),
                "detection_count": int(len(group)),
                "satellite_count": int(group["satellite"].astype(str).nunique()),
                "satellites": ", ".join(sorted(group["satellite"].astype(str).unique())),
                "sources": ", ".join(sorted(group["source"].astype(str).unique())),
                "first_detected_utc": first_time,
                "last_detected_utc": last_time,
                "duration_hours": round((last_time - first_time).total_seconds() / 3600, 2),
                "peak_frp_mw": round(float(frp.max()), 2) if frp.notna().any() else None,
                "mean_frp_mw": round(float(frp.mean()), 2) if frp.notna().any() else None,
                "max_confidence": max_confidence,
                "daynight": ",".join(sorted(group["daynight"].astype(str).unique())),
                "in_wales_watch_bbox": bool(group["in_wales_watch_bbox"].any()),
            }
        )
    incidents = pd.DataFrame.from_records(records, columns=columns)
    return incidents.sort_values(["in_wales_watch_bbox", "last_detected_utc"], ascending=[False, False]).reset_index(drop=True)


def incidents_geojson(incidents: pd.DataFrame) -> dict[str, object]:
    features: list[dict[str, object]] = []
    for row in incidents.to_dict(orient="records"):
        props = dict(row)
        lat = float(props.pop("latitude"))
        lon = float(props.pop("longitude"))
        for key in ("first_detected_utc", "last_detected_utc"):
            value = props.get(key)
            if hasattr(value, "isoformat"):
                props[key] = value.isoformat()
        for key, value in list(props.items()):
            if isinstance(value, float) and math.isnan(value):
                props[key] = None
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": props,
            }
        )
    return {"type": "FeatureCollection", "features": features}


def _format_timestamp(value: object) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def render_map_html(incidents: pd.DataFrame, summary: dict[str, object]) -> str:
    geojson = incidents_geojson(incidents)
    data_json = json.dumps(geojson, separators=(",", ":"))
    summary_json = json.dumps(summary, separators=(",", ":"))
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
  <title>Hinsawdd Cymru | Wildfire Watch</title>
  <link rel=\"stylesheet\" href=\"https://unpkg.com/leaflet@1.9.4/dist/leaflet.css\" crossorigin=\"\">
  <link rel=\"stylesheet\" href=\"https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css\">
  <link rel=\"stylesheet\" href=\"https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css\">
  <style>
    :root {{ color-scheme: dark; --bg:#0b1117; --panel:#111b24; --text:#e7eef5; --muted:#9fb0bf; --accent:#e75f20; }}
    * {{ box-sizing:border-box; }}
    html,body {{ margin:0; background:var(--bg); color:var(--text); font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,\"Segoe UI\",sans-serif; }}
    header {{ padding:18px 20px 12px; background:linear-gradient(180deg,#101b24 0%,#0b1117 100%); border-bottom:1px solid #26333d; }}
    h1 {{ margin:0; font-size:clamp(1.35rem,3vw,2rem); }}
    .subtitle {{ margin-top:5px; color:var(--muted); font-size:.94rem; }}
    .stats {{ display:flex; gap:10px; flex-wrap:wrap; margin-top:13px; }}
    .stat {{ background:var(--panel); border:1px solid #26333d; border-radius:10px; padding:8px 11px; min-width:120px; }}
    .stat strong {{ display:block; font-size:1.15rem; }}
    .stat span {{ color:var(--muted); font-size:.78rem; }}
    #map {{ width:100%; height:calc(100vh - 210px); min-height:520px; }}
    .notice {{ padding:10px 20px 14px; color:var(--muted); font-size:.82rem; border-top:1px solid #26333d; }}
    .fire-icon {{ width:26px!important; height:26px!important; margin-left:-13px!important; margin-top:-13px!important; border-radius:50%; background:#b54117; border:2px solid #fff; color:#fff; display:grid!important; place-items:center; font-size:14px; box-shadow:0 2px 8px #0008; }}
    .fire-icon.wales {{ background:#e75f20; }}
    .marker-cluster-small,.marker-cluster-medium,.marker-cluster-large {{ background:rgba(231,95,32,.34); }}
    .marker-cluster-small div,.marker-cluster-medium div,.marker-cluster-large div {{ background:#b54117; color:white; font-weight:700; }}
    .leaflet-popup-content-wrapper,.leaflet-popup-tip {{ background:#111b24; color:#e7eef5; }}
    .popup-title {{ font-weight:700; margin-bottom:6px; }}
    .popup-grid {{ display:grid; grid-template-columns:auto auto; column-gap:10px; row-gap:3px; font-size:.86rem; }}
    .popup-grid span:nth-child(odd) {{ color:#9fb0bf; }}
    .popup-warning {{ margin-top:8px; padding-top:7px; border-top:1px solid #33424f; color:#ffc8ae; font-size:.78rem; }}
  </style>
</head>
<body>
<header>
  <h1>🔥 Hinsawdd Cymru: Wildfire Watch</h1>
  <div class=\"subtitle\">NASA FIRMS VIIRS thermal-anomaly clusters over the UK, centred on Wales.</div>
  <div class=\"stats\" id=\"stats\"></div>
</header>
<div id=\"map\"></div>
<div class=\"notice\"><strong>Evidence boundary:</strong> a satellite thermal anomaly is not confirmation of a wildfire. Industrial heat, other hot surfaces, cloud/smoke effects and repeat satellite observations can affect the display. The orange Wales watch window is an MVP rectangle, not the legal national boundary.</div>
<script src=\"https://unpkg.com/leaflet@1.9.4/dist/leaflet.js\" crossorigin=\"\"></script>
<script src=\"https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js\"></script>
<script>
const data={data_json};
const summary={summary_json};
const map=L.map('map',{{zoomControl:true}}).setView([52.42,-3.75],7);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{
  maxZoom:19,
  attribution:'&copy; OpenStreetMap contributors'
}}).addTo(map);
const walesBounds=[[{WALES_WATCH_BBOX[1]},{WALES_WATCH_BBOX[0]}],[{WALES_WATCH_BBOX[3]},{WALES_WATCH_BBOX[2]}]];
L.rectangle(walesBounds,{{color:'#e75f20',weight:1,opacity:.7,fill:false,dashArray:'6 6'}}).addTo(map).bindTooltip('Wales watch window (MVP rectangle)');
const markers=L.markerClusterGroup({{showCoverageOnHover:false,maxClusterRadius:42}});
function safe(v){{ if(v===null||v===undefined||v==='') return 'n/a'; return String(v); }}
for(const feature of data.features){{
  const p=feature.properties;
  const c=feature.geometry.coordinates;
  const icon=L.divIcon({{className:'fire-icon'+(p.in_wales_watch_bbox?' wales':''),html:'●',iconSize:[26,26]}});
  const marker=L.marker([c[1],c[0]],{{icon}});
  marker.bindPopup(`<div class=\"popup-title\">${{safe(p.incident_id)}}</div>
    <div class=\"popup-grid\">
      <span>Detections</span><span>${{safe(p.detection_count)}}</span>
      <span>Satellites</span><span>${{safe(p.satellites)}}</span>
      <span>First</span><span>${{safe(p.first_detected_utc)}}</span>
      <span>Latest</span><span>${{safe(p.last_detected_utc)}}</span>
      <span>Peak FRP</span><span>${{safe(p.peak_frp_mw)}} MW</span>
      <span>Confidence</span><span>${{safe(p.max_confidence)}}</span>
    </div><div class=\"popup-warning\">Thermal-anomaly cluster, not a confirmed wildfire.</div>`);
  markers.addLayer(marker);
}}
map.addLayer(markers);
const statItems=[
  [summary.detection_count,'VIIRS detections'],
  [summary.incident_count,'thermal clusters'],
  [summary.wales_watch_incident_count,'in Wales watch window'],
  [summary.source_count,'VIIRS feeds']
];
document.getElementById('stats').innerHTML=statItems.map(([value,label])=>`<div class=\"stat\"><strong>${{safe(value)}}</strong><span>${{label}}</span></div>`).join('');
</script>
</body>
</html>
"""


def build_outputs(
    detections: pd.DataFrame,
    output_root: Path,
    distance_km: float = 5.0,
    time_hours: float = 18.0,
    metadata: dict[str, object] | None = None,
) -> dict[str, object]:
    output_root = Path(output_root)
    derived_dir = output_root / "data" / "derived"
    site_dir = output_root / "site"
    derived_dir.mkdir(parents=True, exist_ok=True)
    site_dir.mkdir(parents=True, exist_ok=True)

    clustered = cluster_detections(detections, distance_km=distance_km, time_hours=time_hours)
    incidents = summarize_incidents(clustered)

    latest = detections["acq_datetime_utc"].max() if not detections.empty else None
    earliest = detections["acq_datetime_utc"].min() if not detections.empty else None
    summary: dict[str, object] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "detection_count": int(len(detections)),
        "incident_count": int(len(incidents)),
        "wales_watch_detection_count": int(detections["in_wales_watch_bbox"].sum()) if not detections.empty else 0,
        "wales_watch_incident_count": int(incidents["in_wales_watch_bbox"].sum()) if not incidents.empty else 0,
        "source_count": int(detections["source"].nunique()) if not detections.empty else 0,
        "sources": sorted(detections["source"].astype(str).unique().tolist()) if not detections.empty else [],
        "earliest_detection_utc": _format_timestamp(earliest),
        "latest_detection_utc": _format_timestamp(latest),
        "cluster_distance_km": distance_km,
        "cluster_time_hours": time_hours,
        "wales_watch_bbox": list(WALES_WATCH_BBOX),
        "status": "satellite thermal anomalies; not confirmed wildfire incidents",
    }
    if metadata:
        summary.update(metadata)

    csv_detections = detections.copy()
    if "acq_datetime_utc" in csv_detections:
        csv_detections["acq_datetime_utc"] = csv_detections["acq_datetime_utc"].map(_format_timestamp)
    csv_clustered = clustered.copy()
    if "acq_datetime_utc" in csv_clustered:
        csv_clustered["acq_datetime_utc"] = csv_clustered["acq_datetime_utc"].map(_format_timestamp)
    csv_incidents = incidents.copy()
    for column in ("first_detected_utc", "last_detected_utc"):
        if column in csv_incidents:
            csv_incidents[column] = csv_incidents[column].map(_format_timestamp)

    csv_detections.to_csv(derived_dir / "detections.csv", index=False)
    csv_clustered.to_csv(derived_dir / "clustered_detections.csv", index=False)
    csv_incidents.to_csv(derived_dir / "incidents.csv", index=False)
    (derived_dir / "incidents.geojson").write_text(
        json.dumps(incidents_geojson(incidents), indent=2), encoding="utf-8"
    )
    (derived_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (site_dir / "index.html").write_text(render_map_html(incidents, summary), encoding="utf-8")
    return summary


def load_retained_csvs(input_dir: Path) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    frames: list[pd.DataFrame] = []
    manifests: list[dict[str, object]] = []
    for path in sorted(Path(input_dir).glob("VIIRS_*_NRT.csv")):
        source = path.stem
        if source not in VIIRS_SOURCES:
            continue
        payload = path.read_bytes()
        frames.append(parse_and_normalize(payload, source))
        manifests.append(
            {
                "source": source,
                "path": str(path),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "mode": "retained",
            }
        )
    if not frames:
        raise FileNotFoundError(f"No retained VIIRS_*_NRT.csv files found in {input_dir}")
    return pd.concat(frames, ignore_index=True), manifests


def fetch_live_sources(
    map_key: str,
    raw_root: Path,
    days: int,
    bbox: tuple[float, float, float, float],
    date: str | None,
) -> tuple[pd.DataFrame, list[dict[str, object]], Path]:
    retrieved_at = datetime.now(timezone.utc)
    snapshot_dir = Path(raw_root) / retrieved_at.strftime("%Y%m%dT%H%M%SZ")
    snapshot_dir.mkdir(parents=True, exist_ok=False)
    frames: list[pd.DataFrame] = []
    manifests: list[dict[str, object]] = []

    with requests.Session() as session:
        session.headers.update({"User-Agent": "hinsawdd-cymru-wildfire-watch/0.1"})
        for source in VIIRS_SOURCES:
            payload, safe_endpoint = fetch_firms_csv(session, map_key, source, bbox, days, date=date)
            output = snapshot_dir / f"{source}.csv"
            output.write_bytes(payload)
            manifest = {
                "source": source,
                "retrieved_at_utc": retrieved_at.isoformat(),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "bytes": len(payload),
                "endpoint": safe_endpoint,
                "bbox": list(bbox),
                "day_range": days,
                "date": date,
            }
            (snapshot_dir / f"{source}.provenance.json").write_text(
                json.dumps(manifest, indent=2), encoding="utf-8"
            )
            manifests.append(manifest)
            frames.append(parse_and_normalize(payload, source))

    combined = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return combined, manifests, snapshot_dir


def parse_bbox(value: str) -> tuple[float, float, float, float]:
    if value.lower() == "uk":
        return UK_BBOX
    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("bbox must be 'uk' or west,south,east,north")
    try:
        bbox = tuple(float(part) for part in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("bbox coordinates must be numeric") from exc
    west, south, east, north = bbox
    if west >= east or south >= north:
        raise argparse.ArgumentTypeError("bbox west/east or south/north ordering is invalid")
    return bbox  # type: ignore[return-value]


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the Hinsawdd Cymru NASA FIRMS wildfire-watch MVP")
    parser.add_argument("--days", type=int, default=2, choices=range(1, 6), metavar="1..5")
    parser.add_argument("--bbox", type=parse_bbox, default=UK_BBOX, help="'uk' or west,south,east,north")
    parser.add_argument("--date", help="Optional historical start date YYYY-MM-DD")
    parser.add_argument("--input-dir", type=Path, help="Rebuild from retained VIIRS_*_NRT.csv files instead of fetching")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--cluster-km", type=float, default=5.0)
    parser.add_argument("--cluster-hours", type=float, default=18.0)
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.input_dir:
        detections, manifests = load_retained_csvs(args.input_dir)
        metadata = {"input_mode": "retained", "input_manifests": manifests}
    else:
        map_key = os.environ.get("NASA_FIRMS_MAP_KEY", "").strip()
        if not map_key:
            parser.error("NASA_FIRMS_MAP_KEY is required for live fetches; or pass --input-dir for retained data")
        detections, manifests, snapshot_dir = fetch_live_sources(
            map_key=map_key,
            raw_root=args.output_root / "data" / "raw",
            days=args.days,
            bbox=args.bbox,
            date=args.date,
        )
        metadata = {
            "input_mode": "live_nrt",
            "snapshot_dir": str(snapshot_dir.relative_to(args.output_root)),
            "input_manifests": manifests,
            "query_bbox": list(args.bbox),
            "query_days": args.days,
            "query_date": args.date,
        }

    summary = build_outputs(
        detections,
        output_root=args.output_root,
        distance_km=args.cluster_km,
        time_hours=args.cluster_hours,
        metadata=metadata,
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
