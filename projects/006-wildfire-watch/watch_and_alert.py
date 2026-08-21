"""6h+ FIRMS watch: on refresh, publish an alert report and push to GitHub.

  python projects/006-wildfire-watch/watch_and_alert.py --minutes 360 --open
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
ALERTS_DIR = ROOT / "ALERTS"


def _run(cmd: list[str], *, cwd: Path | None = None, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd or REPO), check=check, text=True, capture_output=True)


def _load_key() -> str:
    key = os.getenv("NASA_FIRMS_MAP_KEY", "").strip()
    if key:
        return key
    secret = REPO / "secrets" / "nasa firms.txt"
    if secret.exists():
        return secret.read_text().strip().replace("\n", "").replace("\r", "").replace(" ", "")
    raise SystemExit("NASA_FIRMS_MAP_KEY required")


def write_alert(*, baseline_uk: str | None, ping_rc: int) -> Path:
    import pandas as pd

    now = datetime.now(timezone.utc)
    summary_path = ROOT / "published" / "data" / "derived" / "summary.json"
    cand_path = ROOT / "published" / "data" / "derived" / "wales_candidate_locations_corroborated.csv"
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}
    cands = pd.read_csv(cand_path) if cand_path.exists() else pd.DataFrame()

    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    ALERTS_DIR.mkdir(parents=True, exist_ok=True)
    alert_path = ALERTS_DIR / f"ALERT-{stamp}.md"

    top = None
    newest = None
    if len(cands):
        top = cands.sort_values(["detection_count", "peak_frp_mw"], ascending=False).iloc[0]
        newest = cands.sort_values("last_detected_utc", ascending=False).iloc[0]

    def row_bits(row) -> str:
        if row is None:
            return "_none_"
        return (
            f"**{row['community_name']}** — {row['satellite_evidence_band']}, "
            f"{int(row['detection_count'])} dets, peak {float(row['peak_frp_mw']):.1f} MW, "
            f"last {row['last_detected_utc']}"
        )

    body = f"""# FIRMS alert — Wales Wildfire Watch

**Issued:** {now.strftime("%d %B %Y %H:%M UTC")}  
**Type:** automated watch refresh (new VIIRS observations beyond baseline)  
**Severity:** situational awareness — thermal anomalies, **not** confirmed wildfires

## Trigger

| Field | Value |
|---|---|
| Watch baseline UK latest | `{baseline_uk}` |
| New UK latest obs | `{summary.get("latest_detection_utc")}` |
| Snapshot generated | `{summary.get("generated_at_utc")}` |
| Wales-window detections | **{summary.get("wales_watch_detection_count", summary.get("detection_count"))}** |
| Candidate clusters (Wales) | **{len(cands) if len(cands) else summary.get("wales_watch_incident_count")}** |
| `run_all` / ping return code | `{ping_rc}` |

## Top signals this refresh

- **Highest volume cluster:** {row_bits(top)}
- **Newest last-detection cluster:** {row_bits(newest)}

## Maps

- Scientific (locations): [`published/figures/wales_wildfire_watch_dark.png`](../published/figures/wales_wildfire_watch_dark.png)
- Pixels: [`published/figures/wales_firms_pixels_dark.png`](../published/figures/wales_firms_pixels_dark.png)

## Caveat

NASA FIRMS VIIRS NRT detections are provisional. Global NRT latency is often ~1–3 hours. This alert only means **newer satellite observations were published and the local refresh completed** — not that a wildfire has been confirmed on the ground.

See also [CURRENT_SITUATION.md](../CURRENT_SITUATION.md) and [README.md](../README.md).
"""
    alert_path.write_text(body)

    # Rolling pointer + index
    (ALERTS_DIR / "LATEST.md").write_text(body)
    index = ALERTS_DIR / "README.md"
    line = (
        f"- [{stamp}]({alert_path.name}) — UK latest `{summary.get('latest_detection_utc')}` "
        f"· Wales dets {summary.get('wales_watch_detection_count', '?')}\n"
    )
    if index.exists():
        existing = index.read_text()
        if stamp not in existing:
            if "\n- [" in existing or existing.strip().endswith("alerts."):
                # Insert after header block
                if "\n\n" in existing:
                    head, rest = existing.split("\n\n", 1)
                    index.write_text(head + "\n\n" + line + rest)
                else:
                    index.write_text(existing.rstrip() + "\n\n" + line)
            else:
                index.write_text("# Project 006 — FIRMS alerts\n\n" + line + existing)
    else:
        index.write_text(
            "# Project 006 — FIRMS alerts\n\n"
            "Automated refresh alerts from `watch_and_alert.py`.\n\n" + line
        )

    # Point CURRENT_SITUATION at latest alert
    sit = ROOT / "CURRENT_SITUATION.md"
    if sit.exists():
        import re

        text = sit.read_text()
        banner = (
            f"> **Latest automated alert:** [{stamp}](ALERTS/{alert_path.name}) "
            f"(UK latest `{summary.get('latest_detection_utc')}`).\n"
        )
        if "Latest automated alert:" in text:
            text = re.sub(r"> \*\*Latest automated alert:\*\*.+\n", banner, text, count=1)
        else:
            lines = text.splitlines(keepends=True)
            if lines:
                lines.insert(1, "\n" + banner + "\n")
                text = "".join(lines)
        sit.write_text(text)

    return alert_path


def publish_to_github(alert_path: Path) -> None:
    # Refresh README status block if helper available
    pub = ROOT / "publication_status.py"
    if pub.exists():
        subprocess.call(
            [sys.executable, str(pub), "--state", "success"],
            cwd=str(REPO),
        )

    add_paths = [
        "projects/006-wildfire-watch/ALERTS",
        "projects/006-wildfire-watch/CURRENT_SITUATION.md",
        "projects/006-wildfire-watch/README.md",
        "README.md",
        "projects/006-wildfire-watch/published/data/derived",
        "projects/006-wildfire-watch/published/data/reference",
        "projects/006-wildfire-watch/data/history",
        "projects/006-wildfire-watch/published/figures/wales_wildfire_watch_dark.png",
        "projects/006-wildfire-watch/published/figures/wales_wildfire_watch_dark_square.png",
        "projects/006-wildfire-watch/published/figures/wales_firms_pixels_dark.png",
        "projects/006-wildfire-watch/published/figures/wales_firms_pixels_dark_square.png",
        "projects/006-wildfire-watch/published/figures/wales_wildfire_watch_dark.svg",
        "projects/006-wildfire-watch/published/figures/wales_wildfire_watch_dark_square.svg",
        "projects/006-wildfire-watch/published/figures/wales_firms_pixels_dark.svg",
        "projects/006-wildfire-watch/published/figures/wales_firms_pixels_dark_square.svg",
        "projects/006-wildfire-watch/published/site/index.html",
    ]
    # Dated PNG stamps only
    for p in (ROOT / "published" / "figures").glob("*UTC*_dark*.png"):
        add_paths.append(str(p.relative_to(REPO)))
    # Latest raw snapshot dir(s)
    raw_root = ROOT / "published" / "data" / "raw"
    if raw_root.exists():
        newest = sorted([d for d in raw_root.iterdir() if d.is_dir()], reverse=True)[:1]
        for d in newest:
            add_paths.append(str(d.relative_to(REPO)))

    _run(["git", "add", "--", *add_paths])
    stamp = alert_path.stem.replace("ALERT-", "")
    msg = f"Alert: FIRMS refresh {stamp} — update Project 006 maps and alert report."
    status = _run(["git", "status", "--porcelain"])
    if not status.stdout.strip():
        print(json.dumps({"event": "ALERT_NO_GIT_CHANGES", "alert": str(alert_path)}), flush=True)
        return
    _run(["git", "commit", "-m", msg], check=True)
    push = _run(["git", "push", "origin", "HEAD"])
    print(
        json.dumps(
            {
                "event": "ALERT_PUSHED" if push.returncode == 0 else "ALERT_PUSH_FAILED",
                "alert": str(alert_path.relative_to(REPO)),
                "commit_msg": msg,
                "push_stderr": (push.stderr or "")[-500:],
                "returncode": push.returncode,
            },
            indent=2,
        ),
        flush=True,
    )
    if push.returncode != 0:
        raise SystemExit(push.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description="Watch FIRMS then alert+push on refresh")
    parser.add_argument("--minutes", type=float, default=360.0)
    parser.add_argument("--interval", type=float, default=60.0)
    parser.add_argument("--open", action="store_true")
    parser.add_argument("--skip-push", action="store_true", help="Write alert only; do not git push")
    args = parser.parse_args()

    os.environ["NASA_FIRMS_MAP_KEY"] = _load_key()

    # Capture baseline before watch
    sys.path.insert(0, str(ROOT))
    import firms_ping as fp

    baseline_probe = fp.probe(map_key=os.environ["NASA_FIRMS_MAP_KEY"], days=2)
    baseline_uk = baseline_probe.get("uk_latest_obs_utc")

    print(
        json.dumps(
            {
                "event": "WATCH_ALERT_START",
                "minutes": args.minutes,
                "baseline_uk_latest_obs_utc": baseline_uk,
                "started_at_utc": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        ),
        flush=True,
    )

    cmd = [
        sys.executable,
        str(ROOT / "firms_ping.py"),
        "--minutes",
        str(args.minutes),
        "--interval",
        str(args.interval),
        "--run-all",
    ]
    if args.open:
        cmd.append("--open")
    rc = subprocess.call(cmd, cwd=str(REPO), env=os.environ.copy())

    if rc == 2:
        print(json.dumps({"event": "WATCH_ALERT_TIMEOUT", "minutes": args.minutes}), flush=True)
        return 2
    if rc != 0:
        print(json.dumps({"event": "WATCH_ALERT_RUN_FAILED", "returncode": rc}), flush=True)
        return rc

    alert_path = write_alert(baseline_uk=baseline_uk, ping_rc=rc)
    print(json.dumps({"event": "ALERT_WRITTEN", "path": str(alert_path)}), flush=True)
    if not args.skip_push:
        # Ensure we're on main for the publish path
        branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
        if branch != "main":
            print(json.dumps({"event": "ALERT_WARN_NOT_MAIN", "branch": branch}), flush=True)
        publish_to_github(alert_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
