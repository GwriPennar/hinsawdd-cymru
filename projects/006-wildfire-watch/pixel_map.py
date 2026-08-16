"""Render individual NASA FIRMS VIIRS pixels on the official Wales map.

This chart is a companion to the clustered scientific map. Each mark is one
FIRMS thermal-anomaly detection at the latitude/longitude supplied by NASA.
It does not replace cluster-based outputs and is not a confirmed wildfire count.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

import scientific_map as sm

ROOT = Path(__file__).resolve().parent
PIXEL_DPI = 200

CONFIDENCE_COLORS = {
    "low": sm.MUTED,
    "nominal": sm.AMBER,
    "high": sm.PINK,
    "unknown": sm.BLUE,
}

SATELLITE_LABELS = {
    "N": "Suomi NPP",
    "N20": "NOAA-20",
    "N21": "NOAA-21",
}


def detections_inside_wales(
    detections: pd.DataFrame,
    boundary: dict,
    extent: list[float] | None = None,
) -> pd.DataFrame:
    """Keep only detections whose FIRMS coordinates fall inside the official Wales boundary."""
    from matplotlib.path import Path as MplPath

    if detections.empty:
        return detections.copy()

    work = detections.copy()
    work["latitude"] = pd.to_numeric(work["latitude"], errors="coerce")
    work["longitude"] = pd.to_numeric(work["longitude"], errors="coerce")
    work = work.dropna(subset=["latitude", "longitude"]).reset_index(drop=True)

    # Cheap pre-filter using the retained boundary extent before polygon tests.
    if extent is not None and len(extent) == 4:
        min_lon, min_lat, max_lon, max_lat = (float(v) for v in extent)
    else:
        coords = list(sm._all_coordinates(boundary))
        min_lon = float(min(x for x, _ in coords))
        min_lat = float(min(y for _, y in coords))
        max_lon = float(max(x for x, _ in coords))
        max_lat = float(max(y for _, y in coords))
    in_extent = (
        work["longitude"].between(min_lon, max_lon)
        & work["latitude"].between(min_lat, max_lat)
    )
    candidates = work.loc[in_extent].copy()
    if candidates.empty:
        return candidates

    points = candidates[["longitude", "latitude"]].to_numpy(dtype=float)
    assigned = [None] * len(candidates)
    remaining = set(range(len(candidates)))

    for feature in boundary.get("features", []):
        if not remaining:
            break
        name = sm._community_name(feature.get("properties") or {})
        for polygon in sm._iter_rings(feature.get("geometry") or {}):
            if not polygon or not remaining:
                continue
            outer = MplPath([(float(x), float(y)) for x, y, *_ in polygon[0]], closed=True)
            idxs = list(remaining)
            hit = outer.contains_points(points[idxs])
            if not hit.any():
                continue
            holes = [
                MplPath([(float(x), float(y)) for x, y, *_ in hole], closed=True)
                for hole in polygon[1:]
            ]
            for local_i, is_hit in enumerate(hit):
                if not is_hit:
                    continue
                global_i = idxs[local_i]
                if any(hole.contains_point(points[global_i]) for hole in holes):
                    continue
                assigned[global_i] = name
                remaining.discard(global_i)

    keep_mask = [name is not None for name in assigned]
    if not any(keep_mask):
        return candidates.iloc[0:0].copy()

    out = candidates.loc[keep_mask].copy().reset_index(drop=True)
    out["community_name"] = [name for name in assigned if name is not None]
    if "confidence_label" not in out.columns:
        out["confidence_label"] = "unknown"
    out["confidence_label"] = out["confidence_label"].fillna("unknown").astype(str).str.lower()
    out["frp"] = pd.to_numeric(out.get("frp"), errors="coerce")
    return out


def _marker_size(frp, square: bool) -> float:
    base = 22 if square else 18
    if pd.isna(frp):
        return base
    return base + 12 * min(4.0, float(frp) ** 0.5)


def _save_pixel_fig(fig, base: Path) -> None:
    """Save at 2x the usual publication DPI for denser pixel maps."""
    base.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(base.with_suffix(".png"), dpi=PIXEL_DPI, facecolor=sm.FIG_BG, bbox_inches=None)
    fig.savefig(base.with_suffix(".svg"), facecolor=sm.FIG_BG, bbox_inches=None)
    plt.close(fig)


def render_pixel_map(
    pixels: pd.DataFrame,
    boundary: dict,
    manifest: dict,
    summary: dict,
    output_dir: Path,
    square: bool,
) -> None:
    sns.set_theme(context="notebook", style="darkgrid")
    figsize = (10.8, 10.8) if square else (16, 9)
    fig = plt.figure(figsize=figsize, dpi=PIXEL_DPI, facecolor=sm.FIG_BG)

    if square:
        ax = fig.add_axes([0.08, 0.35, 0.84, 0.53])
        panel = fig.add_axes([0.08, 0.08, 0.84, 0.21])
    else:
        ax = fig.add_axes([0.055, 0.11, 0.62, 0.76])
        panel = fig.add_axes([0.70, 0.11, 0.27, 0.76])

    sm._draw_boundary(ax, boundary)
    sm._set_map_axes(ax, manifest["extent"])

    for label in ("low", "nominal", "high", "unknown"):
        group = pixels[pixels["confidence_label"] == label]
        if group.empty:
            continue
        ax.scatter(
            group["longitude"],
            group["latitude"],
            s=[_marker_size(value, square) for value in group["frp"]],
            color=CONFIDENCE_COLORS[label],
            edgecolor=sm.TEXT,
            linewidth=0.4,
            alpha=0.78,
            label=f"{label} ({len(group)})",
            zorder=4,
            rasterized=True,
        )

    # Keep title/subtitle length in the same budget as scientific_map.render_dark_map.
    title = "Wales NASA FIRMS VIIRS pixels"
    subtitle = (
        "NASA FIRMS VIIRS NRT; each mark is one thermal-anomaly pixel at the reported coordinate "
        "inside the official Wales community boundary. Not a confirmed wildfire count."
    )
    left = 0.055 if not square else 0.08
    fig.text(left, 0.95, title, color=sm.TEXT, fontsize=22 if not square else 20, fontweight="bold", ha="left")
    fig.text(left, 0.918, subtitle, color=sm.MUTED, fontsize=10 if not square else 9, ha="left")

    panel.set_facecolor(sm.AX_BG)
    panel.set_xticks([])
    panel.set_yticks([])
    for spine in panel.spines.values():
        spine.set_color(sm.GRID)

    generated = str(summary.get("generated_at_utc", ""))[:16].replace("T", " ")
    latest = str(summary.get("latest_detection_utc", ""))[:16].replace("T", " ")
    heading = 15 if not square else 13
    meta = 10 if not square else 9
    body = 12 if not square else 10.5
    panel.text(
        0.04,
        0.965,
        "Pixel inventory",
        transform=panel.transAxes,
        color=sm.TEXT,
        fontsize=heading,
        fontweight="bold",
        va="top",
    )
    panel.text(
        0.04,
        0.918,
        f"Snapshot {generated} UTC",
        transform=panel.transAxes,
        color=sm.MUTED,
        fontsize=meta,
        va="top",
    )
    panel.text(
        0.04,
        0.875,
        f"Latest observation {latest} UTC",
        transform=panel.transAxes,
        color=sm.MUTED,
        fontsize=meta,
        va="top",
    )

    conf_counts = pixels["confidence_label"].value_counts()
    sat_counts = (
        pixels["satellite"].astype(str).value_counts() if "satellite" in pixels.columns else pd.Series(dtype=int)
    )
    peak_frp = float(pixels["frp"].max()) if len(pixels) and pixels["frp"].notna().any() else 0.0
    mean_frp = float(pixels["frp"].mean()) if len(pixels) and pixels["frp"].notna().any() else 0.0

    # Short stacked lines; larger type than the cluster-map side panel.
    y = 0.80
    rows = [
        (f"Pixels in Wales boundary: {len(pixels):,}", sm.TEXT, True),
        (f"Peak FRP {peak_frp:.1f} MW", sm.MUTED, False),
        (f"Mean FRP {mean_frp:.1f} MW", sm.MUTED, False),
        ("", sm.TEXT, False),
        ("FIRMS confidence", sm.TEXT, True),
    ]
    for label in ("high", "nominal", "low", "unknown"):
        if label in conf_counts.index:
            rows.append((f"{label}: {int(conf_counts[label]):,}", CONFIDENCE_COLORS[label], False))
    rows.append(("", sm.TEXT, False))
    rows.append(("Satellites", sm.TEXT, True))
    for code, count in sat_counts.items():
        rows.append((f"{SATELLITE_LABELS.get(str(code), code)}: {int(count):,}", sm.MUTED, False))

    for text, color, bold in rows:
        if text == "":
            y -= 0.022
            continue
        panel.text(
            0.04,
            y,
            text,
            transform=panel.transAxes,
            color=color,
            fontsize=body,
            fontweight="bold" if bold else "normal",
            va="top",
        )
        y -= 0.055 if bold else 0.045

    handles, labels = ax.get_legend_handles_labels()
    if handles:
        legend = ax.legend(
            handles,
            labels,
            loc="lower left",
            fontsize=9,
            facecolor=sm.AX_BG,
            edgecolor=sm.GRID,
            framealpha=0.95,
            title="FIRMS confidence",
            title_fontsize=10,
        )
        legend.get_title().set_color(sm.TEXT)
        for text in legend.get_texts():
            text.set_color(sm.TEXT)

    footer = (
        "Boundary: Welsh Government DataMapWales, Communities (Wales), derived from OS OpenData Boundary-Line, OGL. "
        "Fire data: NASA FIRMS VIIRS S-NPP, NOAA-20 and NOAA-21 NRT. "
        "Marker size scales with reported FRP; colour is the FIRMS confidence code."
    )
    fig.text(left, 0.025, footer, color=sm.MUTED, fontsize=8 if not square else 7.2, ha="left", va="bottom")

    suffix = "_square" if square else ""
    _save_pixel_fig(fig, Path(output_dir) / f"wales_firms_pixels_dark{suffix}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render NASA FIRMS pixels on the official Wales map")
    parser.add_argument("--output-root", type=Path, default=ROOT)
    parser.add_argument("--detections", type=Path)
    parser.add_argument("--boundary-file", type=Path)
    args = parser.parse_args(argv)

    output_root = Path(args.output_root)
    detections_path = args.detections or output_root / "data" / "derived" / "detections.csv"
    if not detections_path.exists():
        parser.error(f"detections table not found: {detections_path}")

    detections = pd.read_csv(detections_path)
    retained = output_root / "data" / "reference" / "communities_wales.geojson"
    boundary_file = args.boundary_file or (retained if retained.exists() else None)
    boundary, manifest = sm.fetch_or_load_boundary(boundary_file, output_root)
    pixels = detections_inside_wales(detections, boundary, manifest.get("extent"))

    derived = output_root / "data" / "derived"
    figures = output_root / "figures"
    derived.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    pixels.to_csv(derived / "wales_firms_pixels.csv", index=False)

    summary_path = derived / "summary.json"
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}
    summary["official_wales_firms_pixel_count"] = int(len(pixels))
    summary_path.write_text(json.dumps(summary, indent=2))

    for square in (False, True):
        render_pixel_map(pixels, boundary, manifest, summary, figures, square)

    print(
        json.dumps(
            {
                "official_wales_firms_pixel_count": len(pixels),
                "pixel_table": str(derived / "wales_firms_pixels.csv"),
                "figure_stem": str(figures / "wales_firms_pixels_dark"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
