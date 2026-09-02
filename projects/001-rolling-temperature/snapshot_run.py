"""Snapshot an isolated monthly refresh run under runs/YYYY-MM/."""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
DERIVED_DIR = PROJECT_DIR / "data" / "derived"
FIGURES_DIR = PROJECT_DIR / "figures"
RAW_DIR = PROJECT_DIR / "data" / "raw"
RUNS_DIR = PROJECT_DIR / "runs"
INDEX_PATH = RUNS_DIR / "index.json"

DERIVED_FILES = (
    "summary.json",
    "rolling_12_month_mean_temperature.csv",
    "wales_rolling_12_month_temperature_line_chart.csv",
)

FIGURE_STEMS = (
    "wales_rolling_12_month_temperature_history",
    "wales_rolling_12_month_temperature_square_dark",
    "wales_rolling_12_month_temperature_line_chart",
    "wales_rolling_12_month_temperature_line_chart_square_dark",
)

_SVG_DATE_RE = re.compile(r"<dc:date>.*?</dc:date>\n", re.DOTALL)


def _svg_content_equal(left: Path, right: Path) -> bool:
    if not left.exists() or not right.exists():
        return False
    left_text = _SVG_DATE_RE.sub("", left.read_text(encoding="utf-8"))
    right_text = _SVG_DATE_RE.sub("", right.read_text(encoding="utf-8"))
    return left_text == right_text


def _load_index() -> dict[str, object]:
    if not INDEX_PATH.exists():
        return {"runs": []}
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def _write_index(index: dict[str, object]) -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")


def _copy_if_exists(source: Path, destination: Path) -> None:
    if source.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def _copy_raw_snapshot(summary: dict[str, object], run_dir: Path) -> None:
    raw_out = run_dir / "data" / "raw"
    raw_out.mkdir(parents=True, exist_ok=True)
    source_path = PROJECT_DIR / str(summary.get("source_path", ""))
    if source_path.exists():
        _copy_if_exists(source_path, raw_out / source_path.name)
    manifest = summary.get("source_provenance_manifest")
    if manifest:
        manifest_path = PROJECT_DIR / str(manifest)
        _copy_if_exists(manifest_path, raw_out / manifest_path.name)


def _run_markdown(summary: dict[str, object], run_id: str, refreshed_at: str) -> str:
    current = summary["current_window"]
    return f"""# Monthly refresh run {run_id}

**Refreshed:** {refreshed_at}  
**Headline window:** {current['period_label']}  
**Mean temperature:** {current['mean_temperature_c']:.2f}°C  
**Rank:** {current['rank_warmest']} of {current['window_count']} complete monthly-start windows

Source snapshot and figures for this refresh are frozen in this folder. The live report always points at the latest run via `figures/` and `data/derived/`.
"""


def snapshot_run(*, run_id: str | None = None, refreshed_at: str | None = None) -> Path:
    """Copy the latest derived outputs and rolling figures into runs/YYYY-MM/."""

    summary_path = DERIVED_DIR / "summary.json"
    if not summary_path.exists():
        raise FileNotFoundError("Run analysis.py before snapshotting a monthly refresh")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    run_id = run_id or str(summary["last_published_month"])
    refreshed_at = refreshed_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    run_dir = RUNS_DIR / run_id
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True)

    for name in DERIVED_FILES:
        _copy_if_exists(DERIVED_DIR / name, run_dir / "data" / "derived" / name)

    figures_out = run_dir / "figures"
    figures_out.mkdir(parents=True, exist_ok=True)
    for stem in FIGURE_STEMS:
        for suffix in (".png", ".svg"):
            _copy_if_exists(FIGURES_DIR / f"{stem}{suffix}", figures_out / f"{stem}{suffix}")

    _copy_raw_snapshot(summary, run_dir)

    current = summary["current_window"]
    manifest = {
        "run_id": run_id,
        "refreshed_at": refreshed_at,
        "last_published_month": summary["last_published_month"],
        "source_last_updated": summary.get("source_last_updated"),
        "source_snapshot_sha256": summary.get("source_snapshot_sha256"),
        "headline": {
            "period_label": current["period_label"],
            "mean_temperature_c": current["mean_temperature_c"],
            "rank_warmest": current["rank_warmest"],
            "window_count": current["window_count"],
        },
        "paths": {
            "run_dir": f"runs/{run_id}",
            "manifest": f"runs/{run_id}/manifest.json",
            "run_note": f"runs/{run_id}/RUN.md",
        },
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (run_dir / "RUN.md").write_text(_run_markdown(summary, run_id, refreshed_at), encoding="utf-8")

    index = _load_index()
    runs = [entry for entry in index.get("runs", []) if entry.get("run_id") != run_id]
    runs.append(
        {
            "run_id": run_id,
            "refreshed_at": refreshed_at,
            "period_label": current["period_label"],
            "mean_temperature_c": current["mean_temperature_c"],
            "rank_warmest": current["rank_warmest"],
            "window_count": current["window_count"],
            "path": f"runs/{run_id}",
        }
    )
    runs.sort(key=lambda item: item["run_id"], reverse=True)
    index["runs"] = runs
    index["latest_run_id"] = run_id
    _write_index(index)
    return run_dir


def refresh_history_table() -> str:
    index = _load_index()
    runs = index.get("runs", [])
    if not runs:
        return "_No monthly refresh runs recorded yet._"
    rows = [
        "| Run | Headline window | Mean | Rank | Note |",
        "|---|---|---:|---:|---|",
    ]
    for entry in runs:
        rows.append(
            "| [{run_id}](runs/{run_id}/RUN.md) | {period_label} | **{mean:.2f}°C** | {rank} of {total} | [manifest](runs/{run_id}/manifest.json) |".format(
                run_id=entry["run_id"],
                period_label=entry["period_label"],
                mean=entry["mean_temperature_c"],
                rank=entry["rank_warmest"],
                total=entry["window_count"],
            )
        )
    return "\n".join(rows)


def latest_run_matches_live() -> bool:
    """Return True when the latest run snapshot matches live derived data and figures."""

    index = _load_index()
    run_id = index.get("latest_run_id")
    if not run_id:
        return False
    run_dir = RUNS_DIR / str(run_id)
    if not run_dir.exists():
        return False
    for name in DERIVED_FILES:
        live = DERIVED_DIR / name
        snap = run_dir / "data" / "derived" / name
        if not live.exists() or not snap.exists() or live.read_bytes() != snap.read_bytes():
            return False
    for stem in FIGURE_STEMS:
        live_png = FIGURES_DIR / f"{stem}.png"
        snap_png = run_dir / "figures" / f"{stem}.png"
        if not live_png.exists() or not snap_png.exists() or live_png.read_bytes() != snap_png.read_bytes():
            return False
        live_svg = FIGURES_DIR / f"{stem}.svg"
        snap_svg = run_dir / "figures" / f"{stem}.svg"
        if not _svg_content_equal(live_svg, snap_svg):
            return False
    return True
