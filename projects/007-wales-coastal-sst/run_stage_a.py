"""Run Project 007 Stage A: fetch → analyse → figures."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis import analyse
from fetch_hadisst import fetch_hadisst
from fetch_oni import fetch_oni
from figures import render_all


def run(*, skip_fetch: bool = False) -> dict:
    meta: dict = {"stage": "A"}
    if not skip_fetch:
        meta["hadisst"] = fetch_hadisst()
        meta["oni"] = fetch_oni()
    meta["summary"] = analyse()
    meta["figures"] = render_all()
    out = ROOT / "data" / "derived" / "stage_a_run.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta["summary"], indent=2))
    print(f"figures: {len(meta['figures'].get('figures', []))} files")
    return meta


def main() -> int:
    parser = argparse.ArgumentParser(description="Project 007 Stage A pipeline")
    parser.add_argument("--skip-fetch", action="store_true", help="Reuse existing raw files")
    args = parser.parse_args()
    run(skip_fetch=args.skip_fetch)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
