"""Reproducible dark-mode map and location table for Project 006.

The renderer consumes Project 006 incident clusters plus an authoritative Welsh
Government community-boundary GeoJSON. It does not infer a wildfire from a
thermal anomaly. The derived evidence band describes strength of the satellite
thermal evidence only; external confirmation remains a separate future layer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
import pandas as pd
import requests
import seaborn as sns

ROOT = Path(__file__).resolve().parent
DATAMAP_WALES_WFS = "https://datamap.gov.wales/geoserver/ows"
DATAMAP_TYPENAME = "geonode:communites_wales"  # upstream layer identifier is misspelled

FIG_BG = "#080c16"
AX_BG = "#0f172a"
TEXT = "#f8fafc"
MUTED = "#94a3b8"
GRID = "#334155"
CYAN = "#22d3ee"
BLUE = "#60a5fa"
AMBER = "#f59e0b"
PINK = "#fb7185"

EVIDENCE_COLORS = {
    "low": MUTED,
    "plausible": AMBER,
    "strong satellite evidence": PINK,
    "externally confirmed": CYAN,
}

NAME_KEYS = (
    "name_en",
    "name",
    "NAME",
    "community",
    "Community",
    "community_name",
    "NAME_1",
    "label",
)


def _request_boundary(session: requests.Session, timeout: int = 90) -> tuple[bytes, str]:
    params = {
        "service": "WFS",
        "version": "1.0.0",
        "request": "GetFeature",
        "typename": DATAMAP_TYPENAME,
        "outputFormat": "json",
        "srsName": "EPSG:4326",
    }
    response = session.get(DATAMAP_WALES_WFS, params=params, timeout=timeout)
    response.raise_for_status()
    payload = response.content
    if not payload.strip():
        raise RuntimeError("DataMapWales returned an empty Communities (Wales) boundary response")
    safe = (
        f"{DATAMAP_WALES_WFS}?service=WFS&version=1.0.0&request=GetFeature&"
        f"typename={DATAMAP_TYPENAME}&outputFormat=json&srsName=EPSG:4326"
    )
    return payload, safe


def fetch_or_load_boundary(boundary_file: Path | None, output_root: Path) -> tuple[dict, dict]:
    reference_dir = Path(output_root) / "data" / "reference"
    reference_dir.mkdir(parents=True, exist_ok=True)

    if boundary_file is not None:
        payload = Path(boundary_file).read_bytes()
        source = str(boundary_file)
        mode = "retained_fixture"
    else:
        with requests.Session() as session:
            session.headers.update({"User-Agent": "hinsawdd-cymru-wildfire-watch/0.2"})
            payload, source = _request_boundary(session)
        mode = "live_official"
        snapshot = reference_dir / "communities_wales.geojson"
        snapshot.write_bytes(payload)

    try:
        boundary = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Could not parse Communities (Wales) GeoJSON: {exc}") from exc
    if boundary.get("type") != "FeatureCollection" or not boundary.get("features"):
        raise ValueError("Communities (Wales) boundary is not a non-empty GeoJSON FeatureCollection")

    coords = list(_all_coordinates(boundary))
    if not coords:
        raise ValueError("Communities (Wales) boundary contains no polygon coordinates")
    min_lon = min(x for x, _ in coords)
    max_lon = max(x for x, _ in coords)
    min_lat = min(y for _, y in coords)
    max_lat = max(y for _, y in coords)
    if not (-7.5 < min_lon < -2.0 and -6.0 < max_lon < -1.5 and 50.0 < min_lat < 53.0 and 52.5 < max_lat < 54.5):
        raise ValueError(
            "Communities (Wales) boundary coordinates do not look like EPSG:4326 longitude/latitude"
        )

    manifest = {
        "dataset": "Communities (Wales)",
        "organisation": "Welsh Government, Geography & Technology",
        "upstream_layer": DATAMAP_TYPENAME,
        "retrieved_or_loaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "source": source,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
        "crs_requested": "EPSG:4326",
        "licence": "Open Government Licence",
        "contains_os_data": "Contains OS data © Crown copyright and database right 2025",
        "extent": [min_lon, min_lat, max_lon, max_lat],
        "feature_count": len(boundary["features"]),
    }
    (reference_dir / "communities_wales.provenance.json").write_text(json.dumps(manifest, indent=2))
    return boundary, manifest


def _iter_rings(geometry: dict) -> Iterable[list[list[float]]]:
    kind = geometry.get("type")
    coordinates = geometry.get("coordinates") or []
    if kind == "Polygon":
        yield coordinates
    elif kind == "MultiPolygon":
        for polygon in coordinates:
            yield polygon


def _all_coordinates(boundary: dict) -> Iterable[tuple[float, float]]:
    for feature in boundary.get("features", []):
        for polygon in _iter_rings(feature.get("geometry") or {}):
            for ring in polygon:
                for pair in ring:
                    if len(pair) >= 2:
                        yield float(pair[0]), float(pair[1])


def _point_in_ring(lon: float, lat: float, ring: list[list[float]]) -> bool:
    inside = False
    if len(ring) < 3:
        return False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = float(ring[i][0]), float(ring[i][1])
        xj, yj = float(ring[j][0]), float(ring[j][1])
        crosses = (yi > lat) != (yj > lat)
        if crosses:
            x_intersect = (xj - xi) * (lat - yi) / (yj - yi) + xi
            if lon < x_intersect:
                inside = not inside
        j = i
    return inside


def _point_in_polygon(lon: float, lat: float, polygon: list[list[list[float]]]) -> bool:
    if not polygon or not _point_in_ring(lon, lat, polygon[0]):
        return False
    return not any(_point_in_ring(lon, lat, hole) for hole in polygon[1:])


def _feature_contains(feature: dict, lon: float, lat: float) -> bool:
    return any(_point_in_polygon(lon, lat, polygon) for polygon in _iter_rings(feature.get("geometry") or {}))


def _community_name(properties: dict) -> str:
    for key in NAME_KEYS:
        value = properties.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    strings = [
        value.strip()
        for key, value in properties.items()
        if isinstance(value, str) and value.strip() and not key.lower().endswith(("code", "id"))
    ]
    return strings[0] if strings else "Unnamed community"


def locate_community(boundary: dict, lon: float, lat: float) -> str | None:
    for feature in boundary.get("features", []):
        if _feature_contains(feature, lon, lat):
            return _community_name(feature.get("properties") or {})
    return None


def satellite_evidence_band(row: pd.Series) -> str:
    """Classify strength of satellite evidence, not probability of wildfire."""
    detections = int(row.get("detection_count", 0) or 0)
    satellites = int(row.get("satellite_count", 0) or 0)
    confidence = str(row.get("max_confidence", "unknown")).lower()
    peak_frp = pd.to_numeric(pd.Series([row.get("peak_frp_mw")]), errors="coerce").iloc[0]
    peak_frp = float(peak_frp) if pd.notna(peak_frp) else 0.0
    duration = pd.to_numeric(pd.Series([row.get("duration_hours")]), errors="coerce").iloc[0]
    duration = float(duration) if pd.notna(duration) else 0.0

    if confidence == "high" and satellites >= 2 and duration >= 1 and (detections >= 10 or peak_frp >= 20):
        return "strong satellite evidence"
    if confidence in {"high", "nominal"} and (detections >= 2 or satellites >= 2 or peak_frp >= 5):
        return "plausible"
    return "low"


def build_candidate_table(incidents: pd.DataFrame, boundary: dict) -> pd.DataFrame:
    rows = []
    for _, row in incidents.iterrows():
        lon = float(row["longitude"])
        lat = float(row["latitude"])
        community = locate_community(boundary, lon, lat)
        if community is None:
            continue
        record = row.to_dict()
        record["community_name"] = community
        record["satellite_evidence_band"] = satellite_evidence_band(row)
        record["external_confirmation_status"] = "not assessed"
        rows.append(record)
    if not rows:
        return pd.DataFrame(
            columns=list(incidents.columns)
            + ["community_name", "satellite_evidence_band", "external_confirmation_status"]
        )
    out = pd.DataFrame(rows)
    return out.sort_values(["detection_count", "peak_frp_mw"], ascending=[False, False]).reset_index(drop=True)


def _draw_boundary(ax, boundary: dict) -> None:
    for feature in boundary.get("features", []):
        for polygon in _iter_rings(feature.get("geometry") or {}):
            if not polygon:
                continue
            outer = polygon[0]
            xy = [(float(x), float(y)) for x, y, *_ in outer]
            patch = MplPolygon(
                xy,
                closed=True,
                facecolor=AX_BG,
                edgecolor=GRID,
                linewidth=0.28,
                alpha=0.95,
                zorder=1,
            )
            ax.add_patch(patch)


def _marker_size(count: float, square: bool) -> float:
    base = 26 if square else 22
    return base + 20 * math.sqrt(max(1.0, float(count)))


def _set_map_axes(ax, extent: list[float]) -> None:
    min_lon, min_lat, max_lon, max_lat = extent
    dx = max_lon - min_lon
    dy = max_lat - min_lat
    ax.set_xlim(min_lon - dx * 0.035, max_lon + dx * 0.035)
    ax.set_ylim(min_lat - dy * 0.025, max_lat + dy * 0.025)
    ax.set_facecolor(FIG_BG)
    ax.set_aspect(1.55, adjustable="box")
    ax.set_xlabel("Longitude", color=MUTED, fontsize=8)
    ax.set_ylabel("Latitude", color=MUTED, fontsize=8)
    ax.tick_params(colors=MUTED, labelsize=7)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.grid(True, color=GRID, alpha=0.18, linewidth=0.5)
    ax.set_axisbelow(True)


def _save(fig, base: Path) -> None:
    base.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(base.with_suffix(".png"), dpi=100, facecolor=FIG_BG, bbox_inches=None)
    fig.savefig(base.with_suffix(".svg"), facecolor=FIG_BG, bbox_inches=None)
    plt.close(fig)


def render_dark_map(candidates: pd.DataFrame, boundary: dict, manifest: dict, summary: dict, output_dir: Path, square: bool) -> None:
    sns.set_theme(context="notebook", style="darkgrid")
    figsize = (10.8, 10.8) if square else (16, 9)
    fig = plt.figure(figsize=figsize, dpi=100, facecolor=FIG_BG)

    if square:
        ax = fig.add_axes([0.08, 0.35, 0.84, 0.53])
        panel = fig.add_axes([0.08, 0.08, 0.84, 0.21])
    else:
        ax = fig.add_axes([0.055, 0.11, 0.62, 0.76])
        panel = fig.add_axes([0.70, 0.11, 0.27, 0.76])

    _draw_boundary(ax, boundary)
    _set_map_axes(ax, manifest["extent"])

    for band in ("low", "plausible", "strong satellite evidence", "externally confirmed"):
        group = candidates[candidates["satellite_evidence_band"] == band]
        if group.empty:
            continue
        ax.scatter(
            group["longitude"],
            group["latitude"],
            s=[_marker_size(value, square) for value in group["detection_count"]],
            color=EVIDENCE_COLORS[band],
            edgecolor=TEXT,
            linewidth=0.65,
            alpha=0.82,
            label=band,
            zorder=4,
        )

    top_n = 7 if square else 9
    leaders = candidates.head(top_n).copy()
    for rank, (_, row) in enumerate(leaders.iterrows(), start=1):
        ax.text(
            float(row["longitude"]),
            float(row["latitude"]),
            str(rank),
            color=FIG_BG,
            fontsize=7.2 if square else 7.6,
            fontweight="bold",
            ha="center",
            va="center",
            zorder=6,
        )

    title = "Wales satellite thermal-anomaly watch"
    subtitle = (
        "NASA FIRMS VIIRS NRT; circles are heuristic thermal-anomaly clusters inside the official Wales community boundary. "
        "Not a confirmed wildfire count."
    )
    fig.text(0.055 if not square else 0.08, 0.95, title, color=TEXT, fontsize=21 if not square else 19, fontweight="bold", ha="left")
    fig.text(0.055 if not square else 0.08, 0.918, subtitle, color=MUTED, fontsize=9.2 if not square else 8.5, ha="left")

    panel.set_facecolor(AX_BG)
    panel.set_xticks([])
    panel.set_yticks([])
    for spine in panel.spines.values():
        spine.set_color(GRID)

    generated = str(summary.get("generated_at_utc", ""))[:16].replace("T", " ")
    latest = str(summary.get("latest_detection_utc", ""))[:16].replace("T", " ")
    panel.text(0.04, 0.965, "Top candidate locations", transform=panel.transAxes, color=TEXT, fontsize=12, fontweight="bold", va="top")
    panel.text(0.04, 0.925, f"Snapshot {generated} UTC | latest observation {latest} UTC", transform=panel.transAxes, color=MUTED, fontsize=7.5, va="top")

    if square:
        lines = []
        for rank, (_, row) in enumerate(leaders.head(7).iterrows(), start=1):
            label = str(row["community_name"])
            lines.append(
                f"{rank}. {label}: {int(row['detection_count'])} detections, {float(row['peak_frp_mw']):.1f} MW, {row['satellite_evidence_band']}"
            )
        panel.text(0.04, 0.82, "\n".join(lines), transform=panel.transAxes, color=TEXT, fontsize=7.7, va="top", linespacing=1.42)
    else:
        y = 0.86
        for rank, (_, row) in enumerate(leaders.iterrows(), start=1):
            band = str(row["satellite_evidence_band"])
            panel.text(0.04, y, f"{rank}", transform=panel.transAxes, color=EVIDENCE_COLORS[band], fontsize=10, fontweight="bold", va="top")
            panel.text(0.10, y, str(row["community_name"]), transform=panel.transAxes, color=TEXT, fontsize=9, fontweight="bold", va="top")
            panel.text(
                0.10,
                y - 0.035,
                f"{int(row['detection_count'])} detections | {int(row['satellite_count'])} satellites | peak FRP {float(row['peak_frp_mw']):.1f} MW",
                transform=panel.transAxes,
                color=MUTED,
                fontsize=7.2,
                va="top",
            )
            panel.text(0.10, y - 0.066, band, transform=panel.transAxes, color=EVIDENCE_COLORS[band], fontsize=7.2, va="top")
            y -= 0.087

    handles, labels = ax.get_legend_handles_labels()
    if handles:
        legend = ax.legend(
            handles,
            labels,
            loc="lower left",
            fontsize=7.5,
            facecolor=AX_BG,
            edgecolor=GRID,
            framealpha=0.95,
            title="Satellite evidence band",
            title_fontsize=8,
        )
        legend.get_title().set_color(TEXT)
        for text in legend.get_texts():
            text.set_color(TEXT)

    footer = (
        "Boundary: Welsh Government DataMapWales, Communities (Wales), derived from OS OpenData Boundary-Line, OGL. "
        "Fire data: NASA FIRMS VIIRS S-NPP, NOAA-20 and NOAA-21 NRT. "
        "Evidence bands are Hinsawdd Cymru satellite-evidence rules, not wildfire probabilities."
    )
    fig.text(0.055 if not square else 0.08, 0.025, footer, color=MUTED, fontsize=7.2 if not square else 6.7, ha="left", va="bottom")

    suffix = "_square" if square else ""
    _save(fig, Path(output_dir) / f"wales_wildfire_watch_dark{suffix}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render the Project 006 scientific Wales thermal-anomaly map")
    parser.add_argument("--output-root", type=Path, default=ROOT)
    parser.add_argument("--incidents", type=Path)
    parser.add_argument("--boundary-file", type=Path)
    args = parser.parse_args(argv)

    output_root = Path(args.output_root)
    incidents_path = args.incidents or output_root / "data" / "derived" / "incidents.csv"
    if not incidents_path.exists():
        parser.error(f"incident table not found: {incidents_path}")

    incidents = pd.read_csv(incidents_path)
    boundary, manifest = fetch_or_load_boundary(args.boundary_file, output_root)
    candidates = build_candidate_table(incidents, boundary)

    derived = output_root / "data" / "derived"
    figures = output_root / "figures"
    derived.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    candidates.to_csv(derived / "wales_candidate_locations.csv", index=False)

    summary_path = derived / "summary.json"
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}
    summary["official_wales_candidate_cluster_count"] = int(len(candidates))
    summary["boundary_sha256"] = manifest["sha256"]
    summary["boundary_dataset"] = manifest["dataset"]
    summary_path.write_text(json.dumps(summary, indent=2))

    for square in (False, True):
        render_dark_map(candidates, boundary, manifest, summary, figures, square)

    print(
        json.dumps(
            {
                "candidate_clusters_inside_official_wales_boundary": len(candidates),
                "candidate_table": str(derived / "wales_candidate_locations.csv"),
                "figure_stem": str(figures / "wales_wildfire_watch_dark"),
                "boundary_sha256": manifest["sha256"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
