"""Generate figures and retained machine-readable outputs."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from dark_climate_analysis import build_analysis
from dark_climate_constants import LinearFit
from dark_climate_sources import load_source
from dark_climate_summary import build_summary
from dark_figure_dryness import render_dryness, render_raindays
from dark_figure_history import render_history, render_july_history
from dark_figure_projection import render_projection


def write_outputs(rainfall_source: Path, raindays_source: Path, output_dir: Path, derived_dir: Path) -> dict[str, object]:
    rainfall = load_source(rainfall_source, metric="rainfall")
    raindays = load_source(raindays_source, metric="raindays1mm")
    analysis = build_analysis(rainfall, raindays)
    output_dir.mkdir(parents=True, exist_ok=True)
    derived_dir.mkdir(parents=True, exist_ok=True)
    rainfall_periods: pd.DataFrame = analysis["rainfall_periods"]
    july: pd.DataFrame = analysis["july"]
    rainday_periods: pd.DataFrame = analysis["rainday_periods"]
    projection: pd.DataFrame = analysis["projection"]
    fits: dict[str, LinearFit] = analysis["fits"]
    rain_note = (
        "Source: Met Office NCIC, Wales HadUK-Grid 1 km area-average rainfall. "
        f"Updated {rainfall.source_last_updated}. Reference: 1991–2020."
    )
    rainday_note = (
        "Source: Met Office NCIC, Wales HadUK-Grid 1 km area-average rain days ≥1 mm. "
        f"Updated {raindays.source_last_updated}. Reference: 1991–2020."
    )
    projection_note = rain_note + " Statistical continuation; not an official climate projection."
    specs = [
        ("wales_august_to_july_rainfall_history_dark", render_history, rainfall_periods, rain_note),
        ("wales_july_rainfall_history_dark", render_july_history, july, rain_note),
        ("wales_august_to_july_rainfall_dryness_dark", render_dryness, rainfall_periods, rain_note),
        ("wales_august_to_july_raindays_history_dark", render_raindays, rainday_periods, rainday_note),
    ]
    for stem, renderer, data, note in specs:
        renderer(data, output_dir / stem, square=False, source_note=note)
        renderer(data, output_dir / f"{stem}_square", square=True, source_note=note)
    render_projection(rainfall_periods, projection, fits, output_dir / "wales_rainfall_statistical_projection_dark", square=False, source_note=projection_note)
    render_projection(rainfall_periods, projection, fits, output_dir / "wales_rainfall_statistical_projection_dark_square", square=True, source_note=projection_note)
    rainfall_periods.to_csv(derived_dir / "dark_august_to_july_rainfall.csv", index=False, float_format="%.6f")
    july.to_csv(derived_dir / "july_rainfall_history.csv", index=False, float_format="%.6f")
    rainday_periods.to_csv(derived_dir / "august_to_july_raindays1mm.csv", index=False, float_format="%.6f")
    projection.to_csv(derived_dir / "dark_rainfall_statistical_projection.csv", index=False, float_format="%.6f")
    summary = build_summary(analysis, rainfall, raindays)
    (derived_dir / "dark_chart_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary
