"""Run Project 007 Stage B: ODYSSEA fetch → daily analyse → figures."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis_daily import analyse_daily
from fetch_odyssea import fetch_odyssea
from figures_daily import render_all_daily


def run(*, skip_fetch: bool = False, start: str | None = None, end: str | None = None) -> dict:
    meta: dict = {"stage": "B"}
    if not skip_fetch:
        meta["odyssea"] = fetch_odyssea(start=start, end=end)
    meta["summary"] = analyse_daily()
    meta["figures"] = render_all_daily()
    out = ROOT / "data" / "derived" / "stage_b_run.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta["summary"], indent=2))
    print(f"figures: {len(meta['figures'].get('figures', []))} files")
    return meta


def main() -> int:
    parser = argparse.ArgumentParser(description="Project 007 Stage B (ODYSSEA daily) pipeline")
    parser.add_argument("--skip-fetch", action="store_true", help="Reuse existing ODYSSEA extracts")
    parser.add_argument("--start", default=None, help="YYYY-MM-DD fetch start")
    parser.add_argument("--end", default=None, help="YYYY-MM-DD fetch end")
    args = parser.parse_args()
    run(skip_fetch=args.skip_fetch, start=args.start, end=args.end)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
