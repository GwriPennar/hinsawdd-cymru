"""Index of Project 006 publication and local runs.

Use this when choosing which snapshot / sweep / browse set to open or rebuild.

  python projects/006-wildfire-watch/runs_index.py
  python projects/006-wildfire-watch/runs_index.py --json
  python projects/006-wildfire-watch/runs_index.py --kind viirs-browse
  python projects/006-wildfire-watch/runs_index.py --write
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
PUBLISHED = ROOT / "published"
INDEX_PATH = PUBLISHED / "local" / "runs_index.json"


def _mtime_iso(path: Path) -> str | None:
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()


def _safe_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _viirs_simple_name(manifest: dict[str, Any], figs: list[Any]) -> tuple[str, str]:
    """Return (name, alias) for a VIIRS browse stamp."""
    sats = manifest.get("satellites")
    fig_count = len(figs)
    ok = int(manifest.get("ok_count") or 0)
    if fig_count == 0 and ok:
        return "VIIRS grid", "viirs-grid"
    # Simplified NOAA-20 set after feedback
    if sats == ["NOAA20"] or (isinstance(sats, list) and list(sats) == ["NOAA20"]):
        return "VIIRS simple", "viirs-simple"
    if fig_count >= 20 or ok >= 16:
        return "VIIRS full", "viirs-full"
    return "VIIRS browse", "viirs-browse"


def _dedupe_names(runs: list[dict[str, Any]]) -> None:
    """Latest keeps the clean name/alias; older copies are marked historical."""
    seen_alias: dict[str, int] = {}
    for r in runs:  # already newest-first
        alias = r["alias"]
        name = r["name"]
        n = seen_alias.get(alias, 0)
        seen_alias[alias] = n + 1
        r["base_alias"] = alias
        r["historical"] = n > 0
        r["latest_for_alias"] = n == 0
        if n == 0:
            continue
        when = str(r.get("generated_at_utc") or "")
        tag = when[11:16].replace(":", "") if len(when) >= 16 else str(n + 1)
        r["alias"] = f"{alias}-{tag}"
        r["name"] = f"{name} ({tag})"
        r["note"] = "Historical stamp — prefer the latest alias without a time suffix."


def _viirs_description(name: str, manifest: dict[str, Any], figs: list[Any]) -> str:
    date = manifest.get("time_date") or "unknown date"
    sats = manifest.get("satellites")
    sat_txt = ", ".join(sats) if isinstance(sats, list) and sats else "SNPP/NOAA-20/NOAA-21"
    n_figs = len(figs)
    ok = manifest.get("ok_count")
    if name.startswith("VIIRS simple"):
        return (
            f"Simplified GIBS browse for Wales on {date}: NOAA-20 only, five products "
            f"(true colour, AOD, thermal, land-surface temp, false colour) with Wales outlines "
            f"and review.html. {ok or n_figs} frames."
        )
    if name.startswith("VIIRS full"):
        return (
            f"Full GIBS browse experiment for Wales on {date}: all three VIIRS birds × many products "
            f"({n_figs} explained figures). Superseded as default by VIIRS simple after feedback."
        )
    if name.startswith("VIIRS grid"):
        return (
            f"Early GIBS browse for Wales on {date}: contact-sheet / raw pulls only "
            f"(no per-product explained figures). Kept as a historical stamp."
        )
    return f"VIIRS GIBS browse snapshot for {date} ({sat_txt}; {n_figs} figures)."


def collect_runs() -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []

    # National FIRMS publication (build.py → published/)
    summary = _safe_json(PUBLISHED / "data" / "derived" / "summary.json")
    site = PUBLISHED / "site" / "index.html"
    if summary:
        snap = str(summary.get("snapshot_dir") or "")
        stamp = Path(snap).name if snap else "unknown"
        site_summary_match = False
        if site.exists():
            text = site.read_text(errors="replace")
            gen = str(summary.get("generated_at_utc") or "")
            site_summary_match = gen[:19] in text if gen else False
        wales_d = summary.get("wales_watch_detection_count")
        wales_c = summary.get("wales_watch_incident_count")
        latest = summary.get("latest_detection_utc")
        runs.append(
            {
                "name": "Wales map",
                "alias": "wales-map",
                "run_id": f"wales-pub-{stamp}",
                "kind": "wales-publication",
                "label": "Wales FIRMS publication (build + site + maps)",
                "description": (
                    "Canonical national FIRMS publication: UK pull → Wales detections/clusters, "
                    f"Leaflet site, cluster + pixel maps. Latest obs {latest}; "
                    f"{wales_d} Wales-window detections, {wales_c} Wales clusters. "
                    "This is what published/site/index.html tracks."
                ),
                "generated_at_utc": summary.get("generated_at_utc"),
                "latest_obs_utc": summary.get("latest_detection_utc"),
                "path": str(PUBLISHED.relative_to(ROOT)),
                "artifacts": {
                    "summary": "published/data/derived/summary.json",
                    "site": "published/site/index.html",
                    "cluster_map": "published/figures/wales_wildfire_watch_dark.png",
                    "pixel_map": "published/figures/wales_firms_pixels_dark.png",
                    "raw_snapshot": snap or None,
                },
                "stats": {
                    "detections": summary.get("detection_count"),
                    "wales_detections": wales_d,
                    "wales_clusters": wales_c,
                    "incidents": summary.get("incident_count"),
                },
                "site_matches_summary": site_summary_match,
                "site_mtime_utc": _mtime_iso(site),
            }
        )

    # VIIRS GIBS browse stamps
    viirs_root = PUBLISHED / "local" / "viirs-snapshot"
    if viirs_root.exists():
        for stamp_dir in sorted(
            [p for p in viirs_root.iterdir() if p.is_dir() and p.name != "latest"],
            reverse=True,
        ):
            manifest = _safe_json(stamp_dir / "manifest.json") or {}
            figs = manifest.get("explained_figures") or []
            name, alias = _viirs_simple_name(manifest, figs)
            runs.append(
                {
                    "name": name,
                    "alias": alias,
                    "run_id": f"viirs-browse-{stamp_dir.name}",
                    "kind": "viirs-browse",
                    "label": "VIIRS GIBS browse snapshot",
                    "description": _viirs_description(name, manifest, figs),
                    "generated_at_utc": manifest.get("generated_at_utc"),
                    "time_date": manifest.get("time_date"),
                    "path": str(stamp_dir.relative_to(ROOT)),
                    "artifacts": {
                        "manifest": f"{stamp_dir.relative_to(ROOT)}/manifest.json",
                        "review_html": f"{stamp_dir.relative_to(ROOT)}/review.html"
                        if (stamp_dir / "review.html").exists()
                        else None,
                        "explainers": f"{stamp_dir.relative_to(ROOT)}/figures/EXPLAINERS.md"
                        if (stamp_dir / "figures" / "EXPLAINERS.md").exists()
                        else None,
                        "contact_sheet": f"{stamp_dir.relative_to(ROOT)}/{manifest['contact_sheet']}"
                        if manifest.get("contact_sheet")
                        else None,
                    },
                    "stats": {
                        "satellites": manifest.get("satellites"),
                        "themes": manifest.get("themes"),
                        "ok_count": manifest.get("ok_count"),
                        "error_count": manifest.get("error_count"),
                        "figure_count": len(figs),
                    },
                }
            )

    # Swansea / Gower local watch
    sg_summary = _safe_json(PUBLISHED / "local" / "swansea-gower" / "data" / "derived" / "summary.json")
    if sg_summary:
        gen = str(sg_summary.get("generated_at_utc") or "")
        stamp = gen.replace("-", "").replace(":", "")[:15] if gen else "current"
        raw = sg_summary.get("raw_snapshot_dir")
        if raw:
            stamp = Path(str(raw)).name
        det = sg_summary.get("detection_count")
        latest = sg_summary.get("latest_detection_utc")
        hours = sg_summary.get("window_hours")
        runs.append(
            {
                "name": "Gower watch",
                "alias": "gower-watch",
                "run_id": f"swansea-gower-{stamp}",
                "kind": "swansea-gower-watch",
                "label": "Swansea/Gower FIRMS local watch",
                "description": (
                    "Local FIRMS sweep over the Swansea–Gower bbox only (not the national site). "
                    f"Last window {hours}h; {det} detections; latest obs {latest}. "
                    "Used for Langrove / Pontarddulais / Jayplas smoke questions."
                ),
                "generated_at_utc": sg_summary.get("generated_at_utc"),
                "latest_obs_utc": sg_summary.get("latest_detection_utc"),
                "path": "published/local/swansea-gower",
                "artifacts": {
                    "summary": "published/local/swansea-gower/data/derived/summary.json",
                    "detections": "published/local/swansea-gower/data/derived/detections.csv",
                    "map": "published/local/swansea-gower/figures/swansea_gower_firms_dark.png",
                    "raw_snapshot": sg_summary.get("raw_snapshot_dir"),
                },
                "stats": {
                    "window_hours": hours,
                    "detections": det,
                    "incidents": sg_summary.get("incident_count"),
                },
            }
        )

    # Ad-hoc wales-now situational pull
    wales_now = PUBLISHED / "local" / "wales-now"
    if wales_now.exists():
        scan = _safe_json(wales_now / "data" / "derived" / "scan_estimates.json") or {}
        fig = wales_now / "figures" / "wales_now_firms_pixels_dark.png"
        runs.append(
            {
                "name": "Wales now",
                "alias": "wales-now",
                "run_id": "wales-now-latest",
                "kind": "wales-now",
                "label": "Ad-hoc Wales situational pixel pull",
                "description": (
                    "One-off situational Wales FIRMS pixel pull (not the canonical publication). "
                    "Useful for a quick live look; prefer Wales map for the official site/maps."
                ),
                "generated_at_utc": scan.get("generated_at_utc") or _mtime_iso(fig),
                "path": "published/local/wales-now",
                "artifacts": {
                    "pixels": "published/local/wales-now/data/derived/wales_latest_pixels.csv",
                    "map": "published/local/wales-now/figures/wales_now_firms_pixels_dark.png"
                    if fig.exists()
                    else None,
                    "scan_estimates": "published/local/wales-now/data/derived/scan_estimates.json"
                    if (wales_now / "data" / "derived" / "scan_estimates.json").exists()
                    else None,
                },
                "stats": scan or None,
            }
        )

    def sort_key(row: dict[str, Any]) -> str:
        return str(row.get("generated_at_utc") or "")

    runs.sort(key=sort_key, reverse=True)
    _dedupe_names(runs)
    return runs


def build_index() -> dict[str, Any]:
    runs = collect_runs()
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project": "006-wildfire-watch",
        "run_count": len(runs),
        "kinds": sorted({r["kind"] for r in runs}),
        "runs": runs,
        "note": (
            "Simple name/alias = chat handle for the latest of that type. "
            "run_id = immutable historical stamp (folder/time). "
            "Older copies: historical=true and a time-suffixed alias. "
            "Full refresh HTML: published/local/refresh/latest/index.html "
            "(python projects/006-wildfire-watch/run_all.py)."
        ),
        "refresh_html": "published/local/refresh/latest/index.html",
    }


def find_run(index: dict[str, Any], query: str) -> dict[str, Any] | None:
    q = query.strip().lower()
    for r in index["runs"]:
        if q in {
            str(r.get("name", "")).lower(),
            str(r.get("alias", "")).lower(),
            str(r.get("run_id", "")).lower(),
            str(r.get("base_alias", "")).lower(),
        }:
            return r
    for r in index["runs"]:
        if (
            q in str(r.get("alias", "")).lower()
            or q in str(r.get("name", "")).lower()
            or q in str(r.get("run_id", "")).lower()
        ):
            return r
    return None


def print_table(index: dict[str, Any], *, kind: str | None = None, all_history: bool = False) -> None:
    runs = index["runs"]
    if kind:
        runs = [r for r in runs if r["kind"] == kind]
    shown = runs if all_history else [r for r in runs if r.get("latest_for_alias", True)]
    hidden = len(runs) - len(shown)
    head = f"Project 006 runs ({len(shown)} current"
    if hidden and not all_history:
        head += f"; +{hidden} historical — use --all)"
    else:
        head += ")"
    print(f"{head}  ·  indexed {index['generated_at_utc'][:19]}Z\n")
    for r in shown:
        when = str(r.get("generated_at_utc") or r.get("time_date") or "n/a")[:19]
        flag = " [historical]" if r.get("historical") else ""
        print(f"{r.get('name')}  ({r.get('alias')}){flag}")
        print(f"  run_id: {r.get('run_id')}  ·  {when} UTC")
        desc = str(r.get("description") or r.get("label") or "").strip()
        if desc:
            print(f"  {desc}")
        print()
    print("Ask by name/alias for the latest. Use run_id for a specific historical stamp.")
    if hidden and not all_history:
        print("Archives: python projects/006-wildfire-watch/runs_index.py --all")
    print("Full refresh HTML: published/local/refresh/latest/index.html")
    print("  (rebuild: python projects/006-wildfire-watch/run_all.py)")


def main() -> None:
    parser = argparse.ArgumentParser(description="List Project 006 runs (publication, browse, local watches)")
    parser.add_argument("--json", action="store_true", help="Print full JSON index")
    parser.add_argument("--write", action="store_true", help=f"Write {INDEX_PATH.relative_to(ROOT)}")
    parser.add_argument("--kind", help="Filter: wales-publication | viirs-browse | swansea-gower-watch | wales-now")
    parser.add_argument("--get", help="Look up one run by name, alias, or run_id")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Include historical stamps (default lists latest name/alias only)",
    )
    args = parser.parse_args()
    index = build_index()
    if args.write:
        INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        INDEX_PATH.write_text(json.dumps(index, indent=2) + "\n")
    if args.get:
        hit = find_run(index, args.get)
        if not hit:
            raise SystemExit(f"No run matched {args.get!r}")
        print(json.dumps(hit, indent=2))
        return
    if args.json:
        print(json.dumps(index, indent=2))
    else:
        print_table(index, kind=args.kind, all_history=bool(args.all))
        if args.write:
            print(f"\nWrote {INDEX_PATH}")


if __name__ == "__main__":
    main()
