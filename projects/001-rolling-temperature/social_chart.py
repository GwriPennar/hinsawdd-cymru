"""Generate a square dark-mode Seaborn graphic for social sharing.

This module does not recalculate the climate result. It reads the derived
August-to-July series and summary produced by ``analysis.py`` and renders the
same values in a more legible 1:1 presentation.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from figure_style import (
    LABEL_INDIVIDUAL_PERIODS,
    LABEL_REFERENCE_1991_2020,
    LABEL_TRAILING_AVERAGE,
    SOCIAL_FOREGROUND,
    SOCIAL_MUTED,
    SOCIAL_PERIOD_COLOUR,
    SOCIAL_PREVIOUS_HIGH,
)
from trend_charts import PointAnnotation, SocialDarkConfig, SocialHeadline, render_social_dark

PROJECT_DIR = Path(__file__).resolve().parent
DERIVED_DIR = PROJECT_DIR / "data" / "derived"
FIGURES_DIR = PROJECT_DIR / "figures"
SERIES_PATH = DERIVED_DIR / "august_to_july_mean_temperature.csv"
SUMMARY_PATH = DERIVED_DIR / "summary.json"
OUTPUT_BASE = FIGURES_DIR / "wales_august_to_july_mean_temperature_square_dark"


def make_square_dark_figure(
    series: pd.DataFrame,
    output_base: Path,
    *,
    july_2026_c: float,
    status: str,
    reference_1991_2020_c: float,
) -> tuple[Path, Path]:
    """Render a 1080 × 1080 dark social graphic from the derived series."""

    required = {"end_year", "mean_temperature_c"}
    missing = required.difference(series.columns)
    if missing:
        raise ValueError(f"Missing chart columns: {sorted(missing)}")
    if len(series) < 10:
        raise ValueError("At least ten periods are required for the moving average")

    data = series.copy().sort_values("end_year").reset_index(drop=True)
    data["trailing_10_period_mean_c"] = (
        data["mean_temperature_c"].rolling(10, min_periods=10).mean()
    )
    current = data.iloc[-1]
    previous = data.iloc[:-1].nlargest(1, "mean_temperature_c").iloc[0]
    current_kind = "published" if status == "published-inputs" else "illustrative"
    july_kind = "published input" if status == "published-inputs" else "illustrative scenario"

    return render_social_dark(
        data,
        output_base,
        reference_c=reference_1991_2020_c,
        config=SocialDarkConfig(
            label_individual=LABEL_INDIVIDUAL_PERIODS,
            label_average=LABEL_TRAILING_AVERAGE,
            label_reference=LABEL_REFERENCE_1991_2020,
            x_col="end_year",
            y_col="mean_temperature_c",
            trailing_col="trailing_10_period_mean_c",
            previous=PointAnnotation(
                float(previous.end_year),
                float(previous.mean_temperature_c),
                f"Previous high\n2006–07  {previous.mean_temperature_c:.2f}°C",
                color=SOCIAL_PREVIOUS_HIGH,
                fontsize=11,
                fontweight="bold",
                xytext=(-10, 24),
            ),
            current=PointAnnotation(
                float(current.end_year),
                float(current.mean_temperature_c),
                f"2025–26 {current_kind}\n{current.mean_temperature_c:.2f}°C",
                color=SOCIAL_FOREGROUND,
                fontsize=12,
                fontweight="bold",
                xytext=(-12, 24),
            ),
            headline=SocialHeadline(
                title_line1="WALES: AUGUST–JULY MEAN TEMPERATURE",
                title_line2="",
                subtitle="Every equivalent 12-month period from 1884–85 to 2025–26",
                headline_value=f"{current.mean_temperature_c:.2f}°C",
                headline_value_color=SOCIAL_PERIOD_COLOUR,
                claim="2025–26 is the warmest equivalent period in the series",
                note=f"Current point uses July 2026 at {july_2026_c:.1f}°C ({july_kind}).",
                footer1="Source: Met Office Wales monthly HadUK-Grid areal series. Monthly means weighted by calendar days.",
                footer2="Independent derived analysis: Hinsawdd Cymru • github.com/GwriPennar/hinsawdd-cymru",
            ),
            xlim_pad=3.0,
        ),
    )


def main() -> None:
    if not SERIES_PATH.exists() or not SUMMARY_PATH.exists():
        raise FileNotFoundError(
            "Run analysis.py first so the derived series and summary are available"
        )

    series = pd.read_csv(SERIES_PATH)
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    png_path, svg_path = make_square_dark_figure(
        series,
        OUTPUT_BASE,
        july_2026_c=float(summary["july_2026_value_used_c"]),
        status=str(summary["analysis_status"]),
        reference_1991_2020_c=float(
            summary.get(
                "august_to_july_reference_1991_2020_c",
                summary["derived_reference_1991_2020_c"],
            )
        ),
    )
    print(json.dumps({"png": str(png_path), "svg": str(svg_path)}, indent=2))


if __name__ == "__main__":
    main()
