"""Generate dark-mode Wales rainfall, dryness and rain-day climate graphics."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from dark_climate_constants import DARK_BG, FIELD_SPECS, MONTH_COLUMNS, MONTH_NUMBERS, LinearFit, SourceBundle  # noqa: E402,F401
from dark_climate_analysis import build_analysis  # noqa: E402,F401
from dark_climate_outputs import write_outputs  # noqa: E402
from dark_climate_readme import update_readme  # noqa: E402
from dark_climate_sources import load_source  # noqa: E402,F401
from dark_climate_stats import bootstrap_projection, fit_linear, fit_theil_sen, monthly_reference, rolling_august_to_july  # noqa: E402,F401
from dark_figure_dryness import render_dryness, render_raindays  # noqa: E402,F401
from dark_figure_history import render_history, render_july_history  # noqa: E402,F401
from dark_figure_projection import render_projection  # noqa: E402,F401


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rainfall-source", type=Path, required=True)
    parser.add_argument("--raindays-source", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--derived-dir", type=Path, required=True)
    parser.add_argument("--update-readme", action="store_true")
    args = parser.parse_args()
    summary = write_outputs(args.rainfall_source, args.raindays_source, args.output_dir, args.derived_dir)
    if args.update_readme:
        update_readme(summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
