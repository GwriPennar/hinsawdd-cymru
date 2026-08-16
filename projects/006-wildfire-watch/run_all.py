"""Run the full Project 006 refresh, then write one HTML with everything.

  export NASA_FIRMS_MAP_KEY=...
  python projects/006-wildfire-watch/run_all.py
  python projects/006-wildfire-watch/run_all.py --open
  python projects/006-wildfire-watch/run_all.py --report-only --open

Steps (unless --report-only):
  1. Wales map publication (build + maps + links + corroboration + history + status)
  2. Gower watch (24h rolling window)
  3. VIIRS simple GIBS browse (yesterday UTC; also today if useful)
  4. Wales now situational pixel pull (2-day API)
  5. Runs index + all-in-one refresh HTML
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import subprocess
import sys
import webbrowser
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
PUBLISHED = ROOT / "published"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build import SOURCES, UK_BBOX, fetch_firms_csv, parse_and_normalize  # noqa: E402
from local_watch import run_local_watch  # noqa: E402
from refresh_bundle import write_refresh_bundle  # noqa: E402
from runs_index import build_index  # noqa: E402
import pixel_map as pm  # noqa: E402
import scientific_map as sm  # noqa: E402


def _run(cmd: list[str], *, env: dict[str, str] | None = None) -> None:
    print(f"\n>>> {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, check=True, cwd=str(REPO), env=env)


def _env_with_key() -> dict[str, str]:
    env = os.environ.copy()
    key = env.get("NASA_FIRMS_MAP_KEY", "").strip()
    if not key:
        secret = REPO / "secrets" / "nasa firms.txt"
        if secret.exists():
            key = secret.read_text().strip().replace("\n", "").replace("\r", "").replace(" ", "")
            env["NASA_FIRMS_MAP_KEY"] = key
    if not env.get("NASA_FIRMS_MAP_KEY", "").strip():
        raise SystemExit("NASA_FIRMS_MAP_KEY is required (env or secrets/nasa firms.txt)")
    return env


def run_wales_publication(env: dict[str, str]) -> None:
    py = sys.executable
    out = str(PUBLISHED)
    _run([py, str(ROOT / "build.py"), "--days", "2", "--bbox", "uk", "--output-root", out], env=env)
    _run([py, str(ROOT / "scientific_map.py"), "--output-root", out], env=env)
    _run([py, str(ROOT / "pixel_map.py"), "--output-root", out], env=env)
    _run([py, str(ROOT / "stamp_maps.py"), "--output-root", out], env=env)

    spec = importlib.util.spec_from_file_location("location_links", ROOT / "location_links.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    path = PUBLISHED / "data" / "derived" / "wales_candidate_locations.csv"
    mod.add_location_links(pd.read_csv(path)).to_csv(path, index=False)
    print("location links ok")

    _run(
        [
            py,
            str(ROOT / "corroboration.py"),
            "--output-root",
            out,
            "--register",
            str(ROOT / "data" / "reference" / "external_wildfire_incidents.csv"),
        ],
        env=env,
    )
    _run(
        [
            py,
            str(ROOT / "history.py"),
            "--append-detections",
            str(PUBLISHED / "data" / "derived" / "detections.csv"),
        ],
        env=env,
    )
    _run([py, str(ROOT / "publication_status.py"), "--state", "success"], env=env)


def run_gower(env: dict[str, str], *, hours: float = 24.0) -> dict:
    summary = run_local_watch(
        map_key=env["NASA_FIRMS_MAP_KEY"],
        output_root=PUBLISHED / "local" / "swansea-gower",
        hours=hours,
    )
    print(json.dumps({k: summary[k] for k in ("generated_at_utc", "window_hours", "detection_count", "latest_detection_utc")}, indent=2))
    return summary


def run_viirs_simple(*, date: str) -> dict:
    py = sys.executable
    cmd = [
        py,
        str(ROOT / "viirs_snapshot.py"),
        "--date",
        date,
        "--bbox",
        "wales",
        "--satellites",
        "NOAA20",
    ]
    print(f"\n>>> {' '.join(cmd)}", flush=True)
    proc = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, check=True)
    print(proc.stdout)
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"raw": proc.stdout}


def run_wales_now(env: dict[str, str], *, days: int = 2) -> dict:
    key = env["NASA_FIRMS_MAP_KEY"]
    now = datetime.now(timezone.utc)
    out_root = PUBLISHED / "local" / "wales-now"
    figures = out_root / "figures"
    derived = out_root / "data" / "derived"
    raw = out_root / "data" / "raw" / now.strftime("%Y%m%dT%H%M%SZ")
    for p in (figures, derived, raw):
        p.mkdir(parents=True, exist_ok=True)

    frames: list[pd.DataFrame] = []
    with requests.Session() as session:
        session.headers.update({"User-Agent": "hinsawdd-cymru-wales-now/0.3"})
        for source in SOURCES:
            payload, _meta = fetch_firms_csv(session, key, source, UK_BBOX, days=days)
            (raw / f"{source}.csv").write_bytes(payload)
            df = parse_and_normalize(payload, source)
            if len(df):
                frames.append(df)

    dets = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    boundary_path = PUBLISHED / "data" / "reference" / "communities_wales.geojson"
    boundary, bmanifest = sm.fetch_or_load_boundary(boundary_path, PUBLISHED)
    pixels = pm.detections_inside_wales(dets, boundary) if len(dets) else dets.copy()
    pixels.to_csv(derived / "wales_latest_pixels.csv", index=False)

    scan_estimates: list[dict] = []
    try:
        from skyfield.api import Loader, wgs84

        loader = Loader(str(REPO / ".skyfield-cache"))
        ts = loader.timescale()
        stations = loader.tle_file("https://celestrak.org/NORAD/elements/gp.php?GROUP=weather&FORMAT=tle")
        name_map = {
            "VIIRS_SNPP_NRT": "SUOMI NPP",
            "VIIRS_NOAA20_NRT": "NOAA 20",
            "VIIRS_NOAA21_NRT": "NOAA 21",
        }
        wales_centre = wgs84.latlon(52.3, -3.8)

        def hav(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
            r = 6371.0
            p1, p2 = math.radians(lat1), math.radians(lat2)
            dphi, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
            a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
            return 2 * r * math.asin(math.sqrt(a))

        for source, label in name_map.items():
            sub = pixels[pixels["source"] == source] if len(pixels) and "source" in pixels.columns else pd.DataFrame()
            n = len(sub)
            if n == 0:
                continue
            latest = pd.to_datetime(sub["acq_datetime_utc"], utc=True).max().to_pydatetime()
            sat = None
            for sn in [s.name for s in stations]:
                su = sn.upper()
                if ("NPP" in label.upper() and "NPP" in su) or ("20" in label and "NOAA 20" in su) or (
                    "21" in label and "NOAA 21" in su
                ):
                    sat = next(s for s in stations if s.name == sn)
                    break
            best = None
            if sat is not None:
                for minutes in range(-90, 91, 1):
                    dt = latest + timedelta(minutes=minutes)
                    ti = ts.from_datetime(dt)
                    elev = (sat - wales_centre).at(ti).altaz()[0].degrees
                    if elev < 1:
                        continue
                    subp = wgs84.subpoint_of(sat.at(ti))
                    km = hav(52.3, -3.8, subp.latitude.degrees, subp.longitude.degrees)
                    cand = (abs(minutes), dt, elev, km)
                    if best is None or cand[0] < best[0]:
                        best = cand
            scan_estimates.append(
                {
                    "source": source,
                    "label": label,
                    "pixel_count": n,
                    "latest_acq_utc": latest.isoformat(),
                    "estimated_scan_utc": best[1].isoformat() if best else None,
                    "elev_deg": round(best[2], 1) if best else None,
                    "nadir_km": round(best[3], 0) if best else None,
                }
            )
    except Exception as exc:  # noqa: BLE001 — situational; keep pull even if TLEs fail
        scan_estimates = [{"error": str(exc)}]

    (derived / "scan_estimates.json").write_text(
        json.dumps(
            {
                "generated_at_utc": now.isoformat(),
                "query_days": days,
                "estimates": scan_estimates,
                "pixel_count": int(len(pixels)),
                "latest_detection_utc": str(pixels["acq_datetime_utc"].max()) if len(pixels) else None,
            },
            indent=2,
        )
        + "\n"
    )

    import matplotlib.pyplot as plt
    import seaborn as sns

    conf = {"low": sm.MUTED, "nominal": sm.AMBER, "high": sm.PINK, "unknown": sm.BLUE}
    sns.set_theme(context="notebook", style="darkgrid")
    fig = plt.figure(figsize=(16, 9), dpi=160, facecolor=sm.FIG_BG)
    ax = fig.add_axes([0.055, 0.11, 0.62, 0.76])
    panel = fig.add_axes([0.70, 0.11, 0.27, 0.76])
    sm._draw_boundary(ax, boundary)
    sm._set_map_axes(ax, bmanifest["extent"])
    work = pixels.copy()
    if len(work):
        work["confidence_label"] = work.get("confidence_label", "unknown")
        work["confidence_label"] = work["confidence_label"].fillna("unknown").astype(str).str.lower()
        work["frp"] = pd.to_numeric(work.get("frp"), errors="coerce")
        for label in ("low", "nominal", "high", "unknown"):
            g = work[work["confidence_label"] == label]
            if g.empty:
                continue
            sizes = [16 + 10 * min(4.0, (0 if pd.isna(v) else float(v)) ** 0.5) for v in g["frp"]]
            ax.scatter(
                g["longitude"],
                g["latitude"],
                s=sizes,
                color=conf[label],
                edgecolor=sm.TEXT,
                linewidth=0.35,
                alpha=0.8,
                label=f"{label} ({len(g)})",
                zorder=4,
                rasterized=True,
            )
    ax.scatter(
        [-4.07518],
        [51.58871],
        s=120,
        marker="x",
        color=sm.CYAN,
        linewidths=2.2,
        zorder=6,
        label="Langrove (correlated)",
    )
    latest = str(work["acq_datetime_utc"].max())[:16].replace("T", " ") if len(work) else "n/a"
    fig.text(0.055, 0.95, "Wales now — latest FIRMS VIIRS snapshot", color=sm.TEXT, fontsize=21, fontweight="bold")
    fig.text(
        0.055,
        0.912,
        f"Live pull {now.strftime('%d %b %Y %H:%M')} UTC · API day-range {days} · latest pixel obs {latest} UTC",
        color=sm.MUTED,
        fontsize=8.6,
    )
    panel.set_facecolor(sm.AX_BG)
    panel.set_xticks([])
    panel.set_yticks([])
    for sp in panel.spines.values():
        sp.set_color(sm.GRID)
    y = 0.96
    panel.text(0.05, y, "Latest snapshot", transform=panel.transAxes, color=sm.TEXT, fontsize=13, fontweight="bold", va="top")
    y -= 0.055
    panel.text(0.05, y, f"Wales pixels: {len(work):,}", transform=panel.transAxes, color=sm.TEXT, fontsize=10.5, va="top")
    y -= 0.04
    panel.text(0.05, y, f"Latest obs: {latest} UTC", transform=panel.transAxes, color=sm.MUTED, fontsize=9, va="top")
    y -= 0.06
    panel.text(0.05, y, "Estimated scans", transform=panel.transAxes, color=sm.TEXT, fontsize=12, fontweight="bold", va="top")
    y -= 0.05
    for est in scan_estimates:
        if "error" in est:
            panel.text(0.05, y, f"TLE note: {est['error'][:70]}", transform=panel.transAxes, color=sm.MUTED, fontsize=8, va="top")
            break
        scan = est.get("estimated_scan_utc")
        scan_txt = scan[11:16] if scan else "n/a"
        panel.text(
            0.05,
            y,
            f"{est['label']}: {est['pixel_count']} px",
            transform=panel.transAxes,
            color=sm.TEXT,
            fontsize=10,
            fontweight="bold",
            va="top",
        )
        y -= 0.038
        panel.text(
            0.05,
            y,
            f"scan ~{scan_txt} UTC · acq {est['latest_acq_utc'][11:16]}",
            transform=panel.transAxes,
            color=sm.MUTED,
            fontsize=8.5,
            va="top",
        )
        y -= 0.045
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        leg = ax.legend(handles, labels, loc="lower left", fontsize=8, facecolor=sm.AX_BG, edgecolor=sm.GRID, framealpha=0.95)
        for t in leg.get_texts():
            t.set_color(sm.TEXT)
    fig.text(
        0.055,
        0.03,
        "Boundary: DataMapWales Communities (Wales), OGL. Fire data: NASA FIRMS VIIRS NRT. Situational pull — not the canonical publication.",
        color=sm.MUTED,
        fontsize=7.2,
    )
    for stem_name in ("wales_now_firms_pixels_dark", "wales_latest_firms_pixels_dark"):
        stem = figures / stem_name
        fig.savefig(stem.with_suffix(".png"), dpi=160, facecolor=sm.FIG_BG)
        fig.savefig(stem.with_suffix(".svg"), facecolor=sm.FIG_BG)
    plt.close(fig)
    summary = {"generated_at_utc": now.isoformat(), "wales_pixels": int(len(work)), "latest_obs": latest}
    print(json.dumps(summary, indent=2))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Full Project 006 refresh + all-in-one HTML")
    parser.add_argument("--report-only", action="store_true", help="Only rebuild runs index + HTML from existing assets")
    parser.add_argument("--open", action="store_true", help="Open the refresh HTML when done")
    parser.add_argument("--gower-hours", type=float, default=24.0)
    parser.add_argument("--skip-wales", action="store_true")
    parser.add_argument("--skip-gower", action="store_true")
    parser.add_argument("--skip-viirs", action="store_true")
    parser.add_argument("--skip-wales-now", action="store_true")
    args = parser.parse_args()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    env = _env_with_key()

    if not args.report_only:
        if not args.skip_wales:
            print("=== Wales map ===", flush=True)
            run_wales_publication(env)
        if not args.skip_gower:
            print("=== Gower watch ===", flush=True)
            run_gower(env, hours=args.gower_hours)
        if not args.skip_viirs:
            print("=== VIIRS simple ===", flush=True)
            yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            # Prefer complete yesterday; also pull today (may be partial early UTC).
            run_viirs_simple(date=yesterday)
            try:
                run_viirs_simple(date=today)
            except subprocess.CalledProcessError as exc:
                print(f"VIIRS today skipped/failed: {exc}", flush=True)
        if not args.skip_wales_now:
            print("=== Wales now ===", flush=True)
            run_wales_now(env, days=2)

    print("=== Refresh HTML ===", flush=True)
    index = build_index()
    meta = write_refresh_bundle(index, stamp=stamp)
    html_path = (PUBLISHED / "local" / "refresh" / "latest" / "index.html").resolve()
    print(json.dumps(meta, indent=2))
    print(f"\nAll-in-one HTML: {html_path}")
    if args.open:
        webbrowser.open(html_path.as_uri())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
