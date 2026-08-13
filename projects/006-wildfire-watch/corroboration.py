"""External corroboration for Project 006.

Satellite evidence and external incident reports remain separate evidence layers.
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
DEFAULT_REGISTER = ROOT / "data" / "reference" / "external_wildfire_incidents.csv"

SOURCE_WEIGHTS = {
    "fire_service": 4,
    "welsh_government": 4,
    "natural_resources_wales": 4,
    "police": 3,
    "public_broadcaster": 2,
    "reputable_news": 2,
    "other": 1,
}


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*r*math.asin(math.sqrt(a))


def load_register(path=DEFAULT_REGISTER):
    df = pd.read_csv(path)
    for col in ("incident_start_utc", "incident_end_utc", "source_published_utc"):
        df[col] = pd.to_datetime(df[col], utc=True, errors="coerce")
    df["source_weight"] = df["source_class"].map(SOURCE_WEIGHTS).fillna(1).astype(int)
    return df


def temporal_relation(cluster_start, cluster_end, incident_start, incident_end):
    cs = pd.to_datetime(cluster_start, utc=True, errors="coerce")
    ce = pd.to_datetime(cluster_end, utc=True, errors="coerce")
    ins = pd.to_datetime(incident_start, utc=True, errors="coerce")
    ine = pd.to_datetime(incident_end, utc=True, errors="coerce")
    if pd.isna(cs) or pd.isna(ce) or pd.isna(ins):
        return "unknown"
    if pd.isna(ine):
        ine = ins
    pad = pd.Timedelta(hours=24)
    if cs <= ine + pad and ce >= ins - pad:
        return "overlap"
    gap = min(abs((cs-ine).total_seconds()), abs((ce-ins).total_seconds())) / 86400
    return "recent" if gap <= 45 else "historical"


def external_status(matches):
    if matches.empty:
        return "no_current_match"
    overlap = matches[matches.temporal_relation == "overlap"]
    official = overlap[overlap.source_class.isin({"fire_service", "welsh_government", "natural_resources_wales", "police"})]
    if not official.empty:
        return "official_current_match"
    if len(overlap) >= 2 and overlap.source_name.nunique() >= 2:
        return "multiple_source_current_match"
    if not matches[matches.temporal_relation == "recent"].empty:
        return "known_recent_wildfire_site"
    return "no_current_match"


def correlate(candidates, register, radius_km=12.0):
    output, match_rows = [], []
    for _, cluster in candidates.iterrows():
        local = []
        for _, incident in register.iterrows():
            distance = haversine_km(float(cluster.latitude), float(cluster.longitude), float(incident.latitude), float(incident.longitude))
            if distance > radius_km:
                continue
            row = {
                "incident_id": cluster.incident_id,
                "external_incident_id": incident.external_incident_id,
                "incident_name": incident.incident_name,
                "distance_km": round(distance, 3),
                "temporal_relation": temporal_relation(cluster.first_detected_utc, cluster.last_detected_utc, incident.incident_start_utc, incident.incident_end_utc),
                "source_class": incident.source_class,
                "source_name": incident.source_name,
                "source_url": incident.source_url,
                "source_statement": incident.source_statement,
            }
            local.append(row); match_rows.append(row)
        local_df = pd.DataFrame(local)
        record = cluster.to_dict()
        record["external_status"] = external_status(local_df)
        record["external_match_count"] = len(local_df)
        if local_df.empty:
            record["nearest_external_incident"] = ""
            record["nearest_external_distance_km"] = pd.NA
        else:
            nearest = local_df.sort_values("distance_km").iloc[0]
            record["nearest_external_incident"] = nearest.incident_name
            record["nearest_external_distance_km"] = nearest.distance_km
        output.append(record)
    return pd.DataFrame(output), pd.DataFrame(match_rows)


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--output-root", type=Path, default=ROOT)
    p.add_argument("--candidates", type=Path)
    p.add_argument("--register", type=Path, default=DEFAULT_REGISTER)
    p.add_argument("--radius-km", type=float, default=12.0)
    args = p.parse_args(argv)
    candidate_path = args.candidates or args.output_root / "data" / "derived" / "wales_candidate_locations.csv"
    candidates = pd.read_csv(candidate_path)
    register = load_register(args.register)
    correlated, matches = correlate(candidates, register, args.radius_km)
    out = args.output_root / "data" / "derived"; out.mkdir(parents=True, exist_ok=True)
    correlated.to_csv(out / "wales_candidate_locations_corroborated.csv", index=False)
    matches.to_csv(out / "external_corroboration_matches.csv", index=False)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
