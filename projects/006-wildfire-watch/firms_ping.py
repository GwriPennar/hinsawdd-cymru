"""Ping NASA FIRMS until new VIIRS data appears, then run the full refresh.

  python projects/006-wildfire-watch/firms_ping.py
  python projects/006-wildfire-watch/firms_ping.py --minutes 120 --interval 60 --run-all --open

Baseline = newest acq_datetime currently in the UK 2-day FIRMS pull.
Each minute re-queries SNPP + NOAA-20 + NOAA-21. When any detection is newer
than baseline, optionally runs run_all.py and exits.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build import SOURCES, UK_BBOX, fetch_firms_csv, parse_and_normalize  # noqa: E402

SWANSEA_GOWER_BBOX = (-4.35, 51.52, -3.85, 51.72)


def _load_key() -> str:
    key = os.getenv("NASA_FIRMS_MAP_KEY", "").strip()
    if key:
        return key
    secret = REPO / "secrets" / "nasa firms.txt"
    if secret.exists():
        return secret.read_text().strip().replace("\n", "").replace("\r", "").replace(" ", "")
    raise SystemExit("NASA_FIRMS_MAP_KEY is required (env or secrets/nasa firms.txt)")


def probe(*, map_key: str, days: int = 2) -> dict:
    """Return latest observation across UK + Gower for all three VIIRS birds."""
    now = datetime.now(timezone.utc)
    frames = []
    per_source: dict[str, dict] = {}
    errors: dict[str, str] = {}

    with requests.Session() as session:
        session.headers.update({"User-Agent": "hinsawdd-cymru-firms-ping/0.1"})
        for source in SOURCES:
            try:
                payload, _ = fetch_firms_csv(session, map_key, source, UK_BBOX, days)
                df = parse_and_normalize(payload, source)
                label = source.replace("VIIRS_", "").replace("_NRT", "")
                if len(df):
                    latest = str(df["acq_datetime_utc"].max())
                    per_source[label] = {"count": int(len(df)), "latest": latest}
                    frames.append(df)
                else:
                    per_source[label] = {"count": 0, "latest": None}
            except Exception as exc:  # noqa: BLE001
                errors[source] = f"{type(exc).__name__}: {exc}"

        # Gower overlay (same day range)
        gower_latest = None
        gower_count = 0
        try:
            import pandas as pd

            g_frames = []
            for source in SOURCES:
                payload, _ = fetch_firms_csv(session, map_key, source, SWANSEA_GOWER_BBOX, days)
                df = parse_and_normalize(payload, source)
                if len(df):
                    g_frames.append(df)
            if g_frames:
                g = pd.concat(g_frames, ignore_index=True)
                gower_count = int(len(g))
                gower_latest = str(g["acq_datetime_utc"].max())
        except Exception as exc:  # noqa: BLE001
            errors["gower"] = f"{type(exc).__name__}: {exc}"

    latest = None
    total = 0
    if frames:
        import pandas as pd

        all_d = pd.concat(frames, ignore_index=True)
        total = int(len(all_d))
        latest = str(all_d["acq_datetime_utc"].max())

    return {
        "probed_at_utc": now.isoformat(),
        "uk_detection_count": total,
        "uk_latest_obs_utc": latest,
        "gower_detection_count": gower_count,
        "gower_latest_obs_utc": gower_latest,
        "per_source": per_source,
        "errors": errors,
    }


def _newer(candidate: str | None, baseline: str | None) -> bool:
    if not candidate:
        return False
    if not baseline:
        return True
    return candidate > baseline


def main() -> int:
    parser = argparse.ArgumentParser(description="Ping FIRMS until new VIIRS data, then run_all")
    parser.add_argument("--minutes", type=float, default=120.0, help="How long to watch (default 120)")
    parser.add_argument("--interval", type=float, default=60.0, help="Seconds between pings (default 60)")
    parser.add_argument("--days", type=int, default=2, choices=range(1, 6), help="FIRMS day range")
    parser.add_argument("--run-all", action="store_true", help="Run run_all.py when data refreshes")
    parser.add_argument("--open", action="store_true", help="Pass --open to run_all.py")
    parser.add_argument(
        "--baseline",
        help="Optional ISO baseline; default = current UK latest obs at start",
    )
    args = parser.parse_args()

    key = _load_key()
    baseline_probe = probe(map_key=key, days=args.days)
    baseline = args.baseline or baseline_probe.get("uk_latest_obs_utc")
    started = datetime.now(timezone.utc)
    deadline = started.timestamp() + args.minutes * 60.0
    ping_n = 0

    print(
        json.dumps(
            {
                "event": "FIRMS_PING_START",
                "started_at_utc": started.isoformat(),
                "baseline_uk_latest_obs_utc": baseline,
                "baseline_gower_latest_obs_utc": baseline_probe.get("gower_latest_obs_utc"),
                "minutes": args.minutes,
                "interval_s": args.interval,
                "run_all_on_refresh": bool(args.run_all),
            },
            indent=2,
        ),
        flush=True,
    )
    print(
        f"AGENT_LOOP_TICK_firms_ping {json.dumps({'prompt': 'firms ping status', 'n': 0, 'baseline': baseline})}",
        flush=True,
    )

    while True:
        ping_n += 1
        result = probe(map_key=key, days=args.days)
        uk_latest = result.get("uk_latest_obs_utc")
        gower_latest = result.get("gower_latest_obs_utc")
        refreshed = _newer(uk_latest, baseline) or _newer(gower_latest, baseline)

        line = {
            "event": "FIRMS_PING",
            "n": ping_n,
            "probed_at_utc": result["probed_at_utc"],
            "uk_latest_obs_utc": uk_latest,
            "gower_latest_obs_utc": gower_latest,
            "uk_detection_count": result["uk_detection_count"],
            "gower_detection_count": result["gower_detection_count"],
            "per_source": result["per_source"],
            "baseline_uk_latest_obs_utc": baseline,
            "refreshed": refreshed,
            "errors": result["errors"] or None,
        }
        print(json.dumps(line), flush=True)
        print(
            f"AGENT_LOOP_TICK_firms_ping {json.dumps({'prompt': 'firms ping status', 'n': ping_n, 'refreshed': refreshed, 'uk_latest': uk_latest, 'gower_latest': gower_latest})}",
            flush=True,
        )

        if refreshed:
            print(
                json.dumps(
                    {
                        "event": "FIRMS_REFRESHED",
                        "n": ping_n,
                        "baseline_uk_latest_obs_utc": baseline,
                        "uk_latest_obs_utc": uk_latest,
                        "gower_latest_obs_utc": gower_latest,
                    },
                    indent=2,
                ),
                flush=True,
            )
            if args.run_all:
                cmd = [sys.executable, str(ROOT / "run_all.py")]
                if args.open:
                    cmd.append("--open")
                print(f">>> {' '.join(cmd)}", flush=True)
                print("AGENT_LOOP_WAKE_firms_ping {\"prompt\":\"FIRMS refreshed — run_all started\"}", flush=True)
                env = os.environ.copy()
                env["NASA_FIRMS_MAP_KEY"] = key
                rc = subprocess.call(cmd, cwd=str(REPO), env=env)
                print(
                    json.dumps({"event": "RUN_ALL_DONE", "returncode": rc}, indent=2),
                    flush=True,
                )
                return rc
            return 0

        if time.time() >= deadline:
            print(
                json.dumps(
                    {
                        "event": "FIRMS_PING_TIMEOUT",
                        "n": ping_n,
                        "baseline_uk_latest_obs_utc": baseline,
                        "uk_latest_obs_utc": uk_latest,
                        "gower_latest_obs_utc": gower_latest,
                        "minutes": args.minutes,
                    },
                    indent=2,
                ),
                flush=True,
            )
            return 2

        # Sleep until next minute boundary-ish, but at least interval seconds
        time.sleep(max(5.0, float(args.interval)))


if __name__ == "__main__":
    raise SystemExit(main())
