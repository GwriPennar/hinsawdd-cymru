"""Monthly rolling 12-month temperature monitor figures for Project 001."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from figure_style import (
    LABEL_REFERENCE_1991_2020,
    LABEL_ROLLING_AVERAGE,
    LABEL_ROLLING_WINDOWS,
    SOCIAL_PERIOD_COLOUR,
    SOCIAL_PREVIOUS_HIGH,
)
from rolling_line_chart import run as run_rolling_line_chart
from trend_charts import LightTrendConfig, PointAnnotation, SocialDarkConfig, SocialHeadline, render_light_trend, render_social_dark

PROJECT_DIR = Path(__file__).resolve().parent
DERIVED_DIR = PROJECT_DIR / "data" / "derived"
FIGURES_DIR = PROJECT_DIR / "figures"
SERIES_PATH = DERIVED_DIR / "rolling_12_month_mean_temperature.csv"
SUMMARY_PATH = DERIVED_DIR / "summary.json"
HISTORY_BASENAME = FIGURES_DIR / "wales_rolling_12_month_temperature_history"
DARK_BASENAME = FIGURES_DIR / "wales_rolling_12_month_temperature_square_dark"


def _load() -> tuple[pd.DataFrame, dict]:
    series = pd.read_csv(SERIES_PATH, parse_dates=["start_month", "end_month"])
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    return series, summary


def _end_year_fraction(frame: pd.DataFrame) -> pd.Series:
    return frame["end_month"].dt.year + (frame["end_month"].dt.month / 12.0)


def render_history(series: pd.DataFrame, summary: dict, basename: Path = HISTORY_BASENAME) -> tuple[Path, Path]:
    data = series.copy()
    data["end_x"] = _end_year_fraction(data)
    data["trailing_10_window_mean_c"] = data["mean_temperature_c"].rolling(10, min_periods=10).mean()
    current = data.iloc[-1]
    previous = data.iloc[:-1].nlargest(1, "mean_temperature_c").iloc[0]
    period = summary["current_window"]["period_label"]
    return render_light_trend(
        data,
        basename,
        reference_c=float(summary["derived_reference_1991_2020_c"]),
        config=LightTrendConfig(
            title=f"Wales rolling 12-month mean temperature to {period}",
            xlabel="Window end (year)",
            ylabel="Mean temperature (°C)",
            footer=(
                "Source: Met Office Wales monthly HadUK-Grid areal series. "
                "Each point is a complete monthly-start 12-month window. "
                f"Latest window ends {summary['last_published_month']}."
            ),
            label_individual=LABEL_ROLLING_WINDOWS,
            label_average=LABEL_ROLLING_AVERAGE,
            label_reference=LABEL_REFERENCE_1991_2020,
            x_col="end_x",
            y_col="mean_temperature_c",
            trailing_col="trailing_10_window_mean_c",
            previous=PointAnnotation(
                float(previous["end_x"]),
                float(previous.mean_temperature_c),
                f"Previous high\n{previous['period_label']}: {previous.mean_temperature_c:.2f}°C",
            ),
            current=PointAnnotation(
                float(current["end_x"]),
                float(current.mean_temperature_c),
                f"Latest\n{current.mean_temperature_c:.2f}°C",
                xytext=(-10, 18),
            ),
            xlim_pad=0.5,
        ),
    )


def render_dark_square(series: pd.DataFrame, summary: dict, basename: Path = DARK_BASENAME) -> tuple[Path, Path]:
    data = series.copy()
    data["end_x"] = _end_year_fraction(data)
    data["trailing_10_window_mean_c"] = data["mean_temperature_c"].rolling(10, min_periods=10).mean()
    current = data.iloc[-1]
    previous = data.iloc[:-1].nlargest(1, "mean_temperature_c").iloc[0]
    period = summary["current_window"]["period_label"]
    rank = int(summary["current_window"]["rank_warmest"])
    total = int(summary["current_window"]["window_count"])
    return render_social_dark(
        data,
        basename,
        reference_c=float(summary["derived_reference_1991_2020_c"]),
        config=SocialDarkConfig(
            label_individual=LABEL_ROLLING_WINDOWS,
            label_average=LABEL_ROLLING_AVERAGE,
            label_reference=LABEL_REFERENCE_1991_2020,
            x_col="end_x",
            y_col="mean_temperature_c",
            trailing_col="trailing_10_window_mean_c",
            previous=PointAnnotation(
                float(previous["end_x"]),
                float(previous.mean_temperature_c),
                f"Previous high\n{previous['period_label']}: {previous.mean_temperature_c:.2f}°C",
                color=SOCIAL_PREVIOUS_HIGH,
                fontsize=11,
                fontweight="bold",
                xytext=(-10, 24),
            ),
            current=PointAnnotation(
                float(current["end_x"]),
                float(current.mean_temperature_c),
                f"Latest\n{current.mean_temperature_c:.2f}°C",
                fontsize=12,
                fontweight="bold",
                xytext=(-12, 24),
            ),
            headline=SocialHeadline(
                title_line1="WALES: ROLLING 12-MONTH",
                title_line2="MEAN TEMPERATURE",
                subtitle=f"Latest complete window: {period}",
                headline_value=f"{current.mean_temperature_c:.2f}°C",
                headline_value_color=SOCIAL_PERIOD_COLOUR,
                claim=f"Ranks {rank} of {total} complete monthly-start windows",
                note=f"Source updated {summary.get('source_last_updated', 'unknown')}.",
                footer1="Monthly monitor refreshed on published Met Office Wales inputs.",
                footer2="",
            ),
            xlim_pad=0.5,
        ),
    )


def run() -> dict[str, Path]:
    series, summary = _load()
    history_png, history_svg = render_history(series, summary)
    dark_png, dark_svg = render_dark_square(series, summary)
    line_outputs = run_rolling_line_chart()
    return {
        "history_png": history_png,
        "history_svg": history_svg,
        "dark_png": dark_png,
        "dark_svg": dark_svg,
        "line_standard_png": line_outputs["standard_png"],
        "line_standard_svg": line_outputs["standard_svg"],
        "line_dark_png": line_outputs["dark_png"],
        "line_dark_svg": line_outputs["dark_svg"],
        "line_data_csv": line_outputs["data_csv"],
    }


if __name__ == "__main__":
    print(json.dumps({key: str(path) for key, path in run().items()}, indent=2))
