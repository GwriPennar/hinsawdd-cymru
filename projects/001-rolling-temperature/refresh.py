"""Orchestrate Project 001 monthly refresh: analyse, render, snapshot, update README."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from analysis import AnalysisConfig, run as run_analysis, update_readme
from monthly_monitor import run as run_monthly_monitor
from snapshot_run import snapshot_run

PROJECT_DIR = Path(__file__).resolve().parent


def _run_script(relative: str, *args: str) -> None:
    script = PROJECT_DIR / relative
    command = [sys.executable, str(script), *args]
    subprocess.run(command, check=True, cwd=PROJECT_DIR)


def _latest_source() -> tuple[Path, Path]:
    raw_dir = PROJECT_DIR / "data" / "raw"
    sources = sorted(raw_dir.glob("metoffice-wales-tmean-retrieved-*.txt"))
    if not sources:
        raise FileNotFoundError("No retrieved Met Office source snapshot found")
    source = sources[-1]
    manifest = source.with_suffix(".provenance.json")
    return source, manifest


def refresh(*, fetch: bool = False, update_readme_block: bool = True) -> Path:
    if fetch:
        _run_script("fetch_source.py", "--output-dir", "data/raw")

    summary = run_analysis(AnalysisConfig(), refresh=False, update_project_readme=False)

    source, manifest = _latest_source()
    _run_script(
        "verify.py",
        "--source",
        str(source.relative_to(PROJECT_DIR)),
        "--manifest",
        str(manifest.relative_to(PROJECT_DIR)),
        "--require-annual",
        "--primary-summary",
        "data/derived/summary.json",
    )

    run_monthly_monitor()

    run_dir = snapshot_run()
    if update_readme_block:
        update_readme(summary)
    return run_dir


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", help="Download latest Met Office source first")
    parser.add_argument("--no-update-readme", action="store_true")
    args = parser.parse_args()
    run_dir = refresh(fetch=args.fetch, update_readme_block=not args.no_update_readme)
    print(run_dir)


if __name__ == "__main__":
    main()
