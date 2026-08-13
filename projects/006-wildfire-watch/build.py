from __future__ import annotations

import argparse, hashlib, io, json, math, os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent
API = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
SOURCES = ("VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT", "VIIRS_NOAA21_NRT")
VIIRS_SOURCES = SOURCES
UK_BBOX = (-8.8, 49.7, 2.0, 61.0)
WALES_WATCH_BBOX = (-5.6, 51.2, -2.55, 53.5)  # MVP rectangle, not a boundary
REQUIRED = {"latitude", "longitude", "acq_date", "acq_time", "satellite", "instrument", "confidence", "version", "frp", "daynight"}
CONF = {"l": "low", "n": "nominal", "h": "high"}
RANK = {"low": 0, "nominal": 1, "high": 2}


def _bbox_text(bbox):
    return ",".join(f"{x:g}" for x in bbox)


def _inside(lat, lon, bbox=WALES_WATCH_BBOX):
    w, s, e, n = bbox
    return w <= lon <= e and s <= lat <= n


def fetch_firms_csv(session, map_key, source, bbox, days, date=None, timeout=60):
    if source not in SOURCES:
        raise ValueError(f"Unsupported source: {source}")
    if not 1 <= days <= 5:
        raise ValueError("NASA FIRMS Area API day range must be between 1 and 5")
    suffix = f"/{date}" if date else ""
    url = f"{API}/{map_key}/{source}/{_bbox_text(bbox)}/{days}{suffix}"
    safe = f"{API}/{{MAP_KEY}}/{source}/{_bbox_text(bbox)}/{days}{suffix}"
    try:
        response = session.get(url, timeout=timeout)
    except requests.RequestException as exc:
        # Do not include requests' exception text: it may contain the key-bearing URL.
        raise RuntimeError(f"NASA FIRMS request failed for {source}: {type(exc).__name__}") from None
    if not response.ok:
        raise RuntimeError(f"NASA FIRMS request failed for {source}: HTTP {response.status_code}")
    if not response.content.strip():
        raise RuntimeError(f"NASA FIRMS returned an empty response for {source}")
    return response.content, safe


def parse_and_normalize(payload: bytes, source: str) -> pd.DataFrame:
    try:
        frame = pd.read_csv(io.BytesIO(payload))
    except Exception as exc:
        raise ValueError(f"Could not parse FIRMS CSV for {source}: {exc}") from exc
    missing = REQUIRED - set(frame.columns)
    if missing:
        raise ValueError(f"FIRMS CSV for {source} is missing columns: {sorted(missing)}")
    for col in ("latitude", "longitude", "frp"):
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    hhmm = frame["acq_time"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(4)
    frame["acq_datetime_utc"] = pd.to_datetime(frame["acq_date"].astype(str) + " " + hhmm, format="%Y-%m-%d %H%M", errors="coerce", utc=True)
    frame["confidence_label"] = frame["confidence"].astype(str).str.strip().str.lower().map(CONF).fillna("unknown")
    frame["source"] = source
    frame["in_wales_watch_bbox"] = [bool(math.isfinite(float(a)) and math.isfinite(float(b)) and _inside(float(a), float(b))) for a, b in zip(frame.latitude, frame.longitude)]
    frame = frame.dropna(subset=["latitude", "longitude", "acq_datetime_utc"])
    frame = frame[frame.latitude.between(-90, 90) & frame.longitude.between(-180, 180)].copy()
    keep = ["latitude", "longitude", "acq_datetime_utc", "acq_date", "acq_time", "satellite", "instrument", "confidence", "confidence_label", "version", "frp", "daynight", "source", "in_wales_watch_bbox"]
    keep += [x for x in ("bright_ti4", "bright_ti5", "scan", "track") if x in frame.columns]
    return frame[keep].sort_values(["acq_datetime_utc", "latitude", "longitude", "source"]).drop_duplicates(["source", "satellite", "acq_datetime_utc", "latitude", "longitude"]).reset_index(drop=True)


def haversine_km(a, b, c, d):
    r = 6371.0088
    p, q = math.radians(a), math.radians(c)
    dp, dl = math.radians(c-a), math.radians(d-b)
    x = math.sin(dp/2)**2 + math.cos(p)*math.cos(q)*math.sin(dl/2)**2
    return 2*r*math.asin(min(1, math.sqrt(x)))


def cluster_detections(detections: pd.DataFrame, distance_km=5.0, time_hours=18.0) -> pd.DataFrame:
    if detections.empty:
        return detections.assign(cluster_id=pd.Series(dtype="int64"))
    if distance_km <= 0 or time_hours <= 0:
        raise ValueError("Cluster distance and time must be positive")
    work = detections.sort_values("acq_datetime_utc").reset_index(drop=True).copy()
    parent = list(range(len(work)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    def union(i, j):
        a, b = find(i), find(j)
        if a != b: parent[b] = a
    t = work.acq_datetime_utc.tolist(); lat = work.latitude.astype(float).tolist(); lon = work.longitude.astype(float).tolist()
    for i in range(len(work)):
        for j in range(i+1, len(work)):
            if (t[j]-t[i]).total_seconds() > time_hours*3600: break
            if haversine_km(lat[i], lon[i], lat[j], lon[j]) <= distance_km: union(i, j)
    roots = [find(i) for i in range(len(work))]
    ids = {root: n+1 for n, root in enumerate(dict.fromkeys(roots))}
    work["cluster_id"] = [ids[x] for x in roots]
    return work


def _incident_id(group):
    row = group.sort_values(["acq_datetime_utc", "latitude", "longitude", "source"]).iloc[0]
    seed = f"{row.acq_datetime_utc.isoformat()}|{row.latitude:.5f}|{row.longitude:.5f}|{row.source}"
    return f"HC-TA-{row.acq_datetime_utc:%Y%m%d}-{hashlib.sha1(seed.encode()).hexdigest()[:7].upper()}"


def summarize_incidents(clustered: pd.DataFrame) -> pd.DataFrame:
    cols = ["incident_id", "latitude", "longitude", "detection_count", "satellite_count", "satellites", "sources", "first_detected_utc", "last_detected_utc", "duration_hours", "peak_frp_mw", "mean_frp_mw", "max_confidence", "daynight", "in_wales_watch_bbox"]
    if clustered.empty: return pd.DataFrame(columns=cols)
    out = []
    for _, g in clustered.groupby("cluster_id"):
        first, last = g.acq_datetime_utc.min(), g.acq_datetime_utc.max()
        conf = [x for x in g.confidence_label.astype(str) if x in RANK]
        frp = pd.to_numeric(g.frp, errors="coerce")
        out.append({"incident_id": _incident_id(g), "latitude": round(float(g.latitude.mean()), 5), "longitude": round(float(g.longitude.mean()), 5), "detection_count": len(g), "satellite_count": g.satellite.astype(str).nunique(), "satellites": ", ".join(sorted(g.satellite.astype(str).unique())), "sources": ", ".join(sorted(g.source.astype(str).unique())), "first_detected_utc": first, "last_detected_utc": last, "duration_hours": round((last-first).total_seconds()/3600, 2), "peak_frp_mw": round(float(frp.max()), 2) if frp.notna().any() else None, "mean_frp_mw": round(float(frp.mean()), 2) if frp.notna().any() else None, "max_confidence": max(conf, key=RANK.get) if conf else "unknown", "daynight": ",".join(sorted(g.daynight.astype(str).unique())), "in_wales_watch_bbox": bool(g.in_wales_watch_bbox.any())})
    return pd.DataFrame(out, columns=cols).sort_values(["in_wales_watch_bbox", "last_detected_utc"], ascending=[False, False]).reset_index(drop=True)


def incidents_geojson(incidents):
    features = []
    for row in incidents.to_dict("records"):
        lat, lon = float(row.pop("latitude")), float(row.pop("longitude"))
        for k in ("first_detected_utc", "last_detected_utc"):
            if hasattr(row.get(k), "isoformat"): row[k] = row[k].isoformat()
        for k, v in list(row.items()):
            if isinstance(v, float) and math.isnan(v): row[k] = None
        features.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [lon, lat]}, "properties": row})
    return {"type": "FeatureCollection", "features": features}


def render_map_html(incidents, summary):
    data = json.dumps(incidents_geojson(incidents), separators=(",", ":")); stats = json.dumps(summary, separators=(",", ":"))
    return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Hinsawdd Cymru | Wildfire Watch</title><link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"><link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css"><link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css"><style>html,body,#map{{margin:0;height:100%;background:#0b1117}}#map{{height:78vh}}header,.note{{font:14px system-ui;color:#e7eef5;background:#0b1117;padding:14px 18px}}h1{{margin:0 0 4px}}.note{{color:#9fb0bf}}.dot{{background:#e75f20;border:2px solid white;border-radius:50%;width:22px!important;height:22px!important}}</style></head><body><header><h1>🔥 Hinsawdd Cymru: Wildfire Watch</h1><div id="stats"></div></header><div id="map"></div><div class="note"><b>Evidence boundary:</b> a satellite thermal anomaly is not confirmation of a wildfire. The Wales watch window is an MVP rectangle, not the legal national boundary.</div><script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script><script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script><script>const data={data},summary={stats};const map=L.map('map').setView([52.42,-3.75],7);L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{maxZoom:19,attribution:'&copy; OpenStreetMap contributors'}}).addTo(map);L.rectangle([[51.2,-5.6],[53.5,-2.55]],{{color:'#e75f20',weight:1,fill:false,dashArray:'6 6'}}).addTo(map);const group=L.markerClusterGroup();for(const f of data.features){{const p=f.properties,c=f.geometry.coordinates,m=L.marker([c[1],c[0]],{{icon:L.divIcon({{className:'dot',iconSize:[22,22]}})}});m.bindPopup(`<b>${{p.incident_id}}</b><br>Detections: ${{p.detection_count}}<br>Satellites: ${{p.satellites}}<br>Latest: ${{p.last_detected_utc}}<br>Peak FRP: ${{p.peak_frp_mw ?? 'n/a'}} MW<br><br><b>Thermal-anomaly cluster, not a confirmed wildfire.</b>`);group.addLayer(m)}}map.addLayer(group);document.getElementById('stats').textContent=`${{summary.detection_count}} VIIRS detections · ${{summary.incident_count}} thermal clusters · ${{summary.wales_watch_incident_count}} in Wales watch window`;</script></body></html>'''


def _fmt(v):
    return "n/a" if v is None or pd.isna(v) else v.isoformat() if hasattr(v, "isoformat") else str(v)


def build_outputs(detections, output_root: Path, distance_km=5.0, time_hours=18.0, metadata=None):
    output_root = Path(output_root); derived = output_root/"data"/"derived"; site = output_root/"site"; derived.mkdir(parents=True, exist_ok=True); site.mkdir(parents=True, exist_ok=True)
    clustered = cluster_detections(detections, distance_km, time_hours); incidents = summarize_incidents(clustered)
    summary = {"generated_at_utc": datetime.now(timezone.utc).isoformat(), "detection_count": len(detections), "incident_count": len(incidents), "wales_watch_detection_count": int(detections.in_wales_watch_bbox.sum()) if len(detections) else 0, "wales_watch_incident_count": int(incidents.in_wales_watch_bbox.sum()) if len(incidents) else 0, "source_count": detections.source.nunique() if len(detections) else 0, "sources": sorted(detections.source.astype(str).unique().tolist()) if len(detections) else [], "earliest_detection_utc": _fmt(detections.acq_datetime_utc.min()) if len(detections) else "n/a", "latest_detection_utc": _fmt(detections.acq_datetime_utc.max()) if len(detections) else "n/a", "cluster_distance_km": distance_km, "cluster_time_hours": time_hours, "wales_watch_bbox": list(WALES_WATCH_BBOX), "status": "satellite thermal anomalies; not confirmed wildfire incidents"}
    if metadata: summary.update(metadata)
    a= detections.copy(); b=clustered.copy(); c=incidents.copy()
    if "acq_datetime_utc" in a: a["acq_datetime_utc"] = a.acq_datetime_utc.map(_fmt)
    if "acq_datetime_utc" in b: b["acq_datetime_utc"] = b.acq_datetime_utc.map(_fmt)
    for col in ("first_detected_utc", "last_detected_utc"):
        if col in c: c[col] = c[col].map(_fmt)
    a.to_csv(derived/"detections.csv", index=False); b.to_csv(derived/"clustered_detections.csv", index=False); c.to_csv(derived/"incidents.csv", index=False)
    (derived/"incidents.geojson").write_text(json.dumps(incidents_geojson(incidents), indent=2)); (derived/"summary.json").write_text(json.dumps(summary, indent=2)); (site/"index.html").write_text(render_map_html(incidents, summary))
    return summary


def load_retained_csvs(input_dir: Path):
    frames=[]; manifests=[]
    for path in sorted(Path(input_dir).glob("VIIRS_*_NRT.csv")):
        if path.stem not in SOURCES: continue
        payload=path.read_bytes(); frames.append(parse_and_normalize(payload, path.stem)); manifests.append({"source": path.stem, "path": str(path), "sha256": hashlib.sha256(payload).hexdigest(), "mode": "retained"})
    if not frames: raise FileNotFoundError(f"No retained VIIRS_*_NRT.csv files found in {input_dir}")
    return pd.concat(frames, ignore_index=True), manifests


def fetch_live_sources(map_key, raw_root, days, bbox, date):
    now=datetime.now(timezone.utc); snapshot=Path(raw_root)/now.strftime("%Y%m%dT%H%M%SZ"); snapshot.mkdir(parents=True, exist_ok=False); frames=[]; manifests=[]
    with requests.Session() as session:
        session.headers.update({"User-Agent":"hinsawdd-cymru-wildfire-watch/0.1"})
        for source in SOURCES:
            payload, safe=fetch_firms_csv(session,map_key,source,bbox,days,date); (snapshot/f"{source}.csv").write_bytes(payload)
            manifest={"source":source,"retrieved_at_utc":now.isoformat(),"sha256":hashlib.sha256(payload).hexdigest(),"bytes":len(payload),"endpoint":safe,"bbox":list(bbox),"day_range":days,"date":date}; (snapshot/f"{source}.provenance.json").write_text(json.dumps(manifest,indent=2)); manifests.append(manifest); frames.append(parse_and_normalize(payload,source))
    return pd.concat(frames,ignore_index=True), manifests, snapshot


def parse_bbox(value):
    if value.lower()=="uk": return UK_BBOX
    try: bbox=tuple(float(x.strip()) for x in value.split(","))
    except ValueError as exc: raise argparse.ArgumentTypeError("bbox coordinates must be numeric") from exc
    if len(bbox)!=4 or bbox[0]>=bbox[2] or bbox[1]>=bbox[3]: raise argparse.ArgumentTypeError("bbox must be west,south,east,north")
    return bbox


def main(argv=None):
    p=argparse.ArgumentParser(description="Build the Hinsawdd Cymru NASA FIRMS wildfire-watch MVP"); p.add_argument("--days",type=int,default=2,choices=range(1,6)); p.add_argument("--bbox",type=parse_bbox,default=UK_BBOX); p.add_argument("--date"); p.add_argument("--input-dir",type=Path); p.add_argument("--output-root",type=Path,default=ROOT); p.add_argument("--cluster-km",type=float,default=5.0); p.add_argument("--cluster-hours",type=float,default=18.0); args=p.parse_args(argv)
    if args.input_dir: detections, manifests=load_retained_csvs(args.input_dir); meta={"input_mode":"retained","input_manifests":manifests}
    else:
        key=os.environ.get("NASA_FIRMS_MAP_KEY","").strip()
        if not key: p.error("NASA_FIRMS_MAP_KEY is required for live fetches; or pass --input-dir")
        detections, manifests, snapshot=fetch_live_sources(key,args.output_root/"data"/"raw",args.days,args.bbox,args.date); meta={"input_mode":"live_nrt","snapshot_dir":str(snapshot.relative_to(args.output_root)),"input_manifests":manifests,"query_bbox":list(args.bbox),"query_days":args.days,"query_date":args.date}
    print(json.dumps(build_outputs(detections,args.output_root,args.cluster_km,args.cluster_hours,meta),indent=2)); return 0


if __name__ == "__main__": raise SystemExit(main())
