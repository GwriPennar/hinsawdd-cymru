"""Animate Wales VIIRS heat anomalies from the cumulative history as a dark GIF.

One frame per UTC day from the history start (default 15 June 2026) at 4 fps.
No legend — date + count only. Marks are FIRMS thermal anomalies, not confirmed wildfires.

  python projects/006-wildfire-watch/history_gif.py
  python projects/006-wildfire-watch/history_gif.py --fps 4 --open
"""
from __future__ import annotations

import argparse
import io
import subprocess
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from PIL import Image

ROOT = Path(__file__).resolve().parent
import sys

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pixel_map as pm
import scientific_map as sm

HISTORY = ROOT / "data" / "history" / "detections.csv"
DEFAULT_START = date(2026, 6, 15)
DEFAULT_OUT = ROOT / "published" / "figures" / "wales_heat_anomalies_history_dark.gif"


def _load_history(path: Path, *, start: date) -> pd.DataFrame:
    raw = pd.read_csv(path)
    raw["acq_datetime_utc"] = pd.to_datetime(raw["acq_datetime_utc"], utc=True, errors="coerce")
    raw["acq_day"] = raw["acq_datetime_utc"].dt.floor("D")
    start_ts = pd.Timestamp(datetime(start.year, start.month, start.day, tzinfo=timezone.utc))
    return raw.loc[raw["acq_day"] >= start_ts].copy()


def _wales_pixels(detections: pd.DataFrame) -> tuple[pd.DataFrame, dict, dict]:
    """Keep Wales-watch detections and load the official boundary for the basemap."""
    import json

    retained = ROOT / "published" / "data" / "reference" / "communities_wales.geojson"
    provenance = ROOT / "published" / "data" / "reference" / "communities_wales.provenance.json"
    if retained.exists():
        boundary = json.loads(retained.read_text())
        manifest = json.loads(provenance.read_text()) if provenance.exists() else {}
        if "extent" not in manifest:
            boundary, manifest = sm.fetch_or_load_boundary(retained, ROOT / "published")
    else:
        boundary, manifest = sm.fetch_or_load_boundary(None, ROOT / "published")

    work = detections.copy()
    if "in_wales_watch_bbox" in work.columns:
        pixels = work.loc[work["in_wales_watch_bbox"].astype(bool)].copy()
    else:
        pixels = pm.detections_inside_wales(work, boundary, manifest.get("extent"))

    if not pixels.empty:
        pixels["acq_datetime_utc"] = pd.to_datetime(pixels["acq_datetime_utc"], utc=True, errors="coerce")
        pixels["acq_day"] = pixels["acq_datetime_utc"].dt.floor("D")
        pixels["frp"] = pd.to_numeric(pixels.get("frp"), errors="coerce")
        pixels["longitude"] = pd.to_numeric(pixels["longitude"], errors="coerce")
        pixels["latitude"] = pd.to_numeric(pixels["latitude"], errors="coerce")
        pixels = pixels.dropna(subset=["longitude", "latitude", "acq_day"])
    return pixels, boundary, manifest


def _day_range(pixels: pd.DataFrame, start: date, end: date | None) -> list[pd.Timestamp]:
    if pixels.empty:
        last = end or start
        first = start
    else:
        first = max(start, pixels["acq_day"].min().date())
        last = end or pixels["acq_day"].max().date()
    days: list[pd.Timestamp] = []
    cur = first
    while cur <= last:
        days.append(pd.Timestamp(datetime(cur.year, cur.month, cur.day, tzinfo=timezone.utc)))
        cur += timedelta(days=1)
    return days


def _sizes(frp: pd.Series) -> np.ndarray:
    values = pd.to_numeric(frp, errors="coerce").fillna(1.0).clip(lower=0.1).to_numpy(dtype=float)
    peak = float(values.max()) if len(values) else 1.0
    return 18.0 + 28.0 * np.sqrt(values / (peak if peak > 0 else 1.0))


def build_gif(
    *,
    history_path: Path = HISTORY,
    start: date = DEFAULT_START,
    end: date | None = None,
    fps: float = 4.0,
    trail_days: int = 2,
    output: Path = DEFAULT_OUT,
) -> dict:
    history = _load_history(history_path, start=start)
    pixels, boundary, manifest = _wales_pixels(history)
    days = _day_range(pixels, start, end)
    print(f"Basemap once · {len(days)} frames · {len(pixels)} Wales-watch detections", flush=True)

    sns.set_theme(context="notebook", style="darkgrid")
    fig = plt.figure(figsize=(12.8, 7.2), dpi=100, facecolor=sm.FIG_BG)
    ax = fig.add_axes([0.04, 0.06, 0.92, 0.86])
    sm._draw_boundary(ax, boundary)
    sm._set_map_axes(ax, manifest["extent"])
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(labelbottom=False, labelleft=False, length=0)
    ax.grid(False)

    title = fig.text(0.05, 0.955, "Wales · VIIRS heat anomalies", color=sm.TEXT, fontsize=18, fontweight="bold", ha="left")
    date_text = fig.text(0.05, 0.915, "", color=sm.CYAN, fontsize=14, ha="left")
    count_text = fig.text(0.95, 0.915, "", color=sm.MUTED, fontsize=11, ha="right")
    fig.text(
        0.05,
        0.02,
        "NASA FIRMS VIIRS NRT · thermal anomalies, not confirmed wildfires · Hinsawdd Cymru Project 006",
        color=sm.MUTED,
        fontsize=7.5,
        ha="left",
    )

    trail_artist = None
    day_artist = None
    frames: list[Image.Image] = []

    for i, day in enumerate(days, start=1):
        day_pixels = pixels.loc[pixels["acq_day"] == day] if not pixels.empty else pixels
        if trail_days > 0 and not pixels.empty:
            trail_start = day - pd.Timedelta(days=trail_days)
            trail = pixels.loc[(pixels["acq_day"] >= trail_start) & (pixels["acq_day"] < day)]
        else:
            trail = pixels.iloc[0:0]

        if trail_artist is not None:
            trail_artist.remove()
            trail_artist = None
        if day_artist is not None:
            day_artist.remove()
            day_artist = None

        if not trail.empty:
            trail_artist = ax.scatter(
                trail["longitude"],
                trail["latitude"],
                s=10,
                c=sm.MUTED,
                alpha=0.28,
                linewidths=0,
                zorder=3,
            )
        if not day_pixels.empty:
            day_artist = ax.scatter(
                day_pixels["longitude"],
                day_pixels["latitude"],
                s=_sizes(day_pixels["frp"]),
                c=sm.AMBER,
                alpha=0.9,
                edgecolors=sm.TEXT,
                linewidths=0.25,
                zorder=4,
            )

        date_text.set_text(day.strftime("%d %b %Y").upper())
        n = int(len(day_pixels))
        count_text.set_text(f"{n} detection{'s' if n != 1 else ''}")

        buf = io.BytesIO()
        fig.savefig(buf, format="png", facecolor=sm.FIG_BG)
        buf.seek(0)
        frames.append(Image.open(buf).convert("P", palette=Image.ADAPTIVE, colors=128))
        if i == 1 or i % 10 == 0 or i == len(days):
            print(f"  frame {i}/{len(days)} {day.date()}", flush=True)

    plt.close(fig)

    if not frames:
        raise SystemExit("No frames to write")

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    duration_ms = int(round(1000.0 / max(fps, 0.1)))
    frames[0].save(
        output,
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,
        optimize=False,
    )

    return {
        "output": str(output),
        "frames": len(frames),
        "fps": fps,
        "start": days[0].date().isoformat(),
        "end": days[-1].date().isoformat(),
        "wales_detection_count": int(len(pixels)),
        "history_rows_loaded": int(len(history)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Wales heat-anomaly history GIF")
    parser.add_argument("--history", type=Path, default=HISTORY)
    parser.add_argument("--start", default=DEFAULT_START.isoformat(), help="UTC start date YYYY-MM-DD")
    parser.add_argument("--end", default=None, help="UTC end date YYYY-MM-DD (default: last history day)")
    parser.add_argument("--fps", type=float, default=4.0)
    parser.add_argument("--trail-days", type=int, default=2, help="Faint previous days (0 = off)")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()

    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end) if args.end else None
    meta = build_gif(
        history_path=args.history,
        start=start,
        end=end,
        fps=args.fps,
        trail_days=args.trail_days,
        output=args.output,
    )
    print(meta)
    if args.open:
        subprocess.run(["open", meta["output"]], check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
