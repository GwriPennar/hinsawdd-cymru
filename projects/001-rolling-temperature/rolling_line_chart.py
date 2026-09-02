"""Rolling 12-month line-chart variants (standard + dark square)."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D

from equivalent_period_chart import gaussian_smooth
from figure_style import (
    DARK_LINE_BACKGROUND,
    DARK_LINE_FOREGROUND,
    DARK_LINE_FRAME,
    DARK_LINE_GRID,
    DARK_LINE_LATEST,
    DARK_LINE_MUTED,
    DARK_LINE_PERIOD_COLOUR,
    DARK_LINE_PREVIOUS_HIGH,
    DARK_LINE_REFERENCE_COLOUR,
    DARK_LINE_TREND_COLOUR,
    LABEL_REFERENCE_1991_2020,
    LABEL_ROLLING_WINDOWS,
    LINE_CHART_DPI,
    SQUARE_PX,
    STANDARD_HEIGHT_PX,
    STANDARD_WIDTH_PX,
)
from line_chart_variants import _save

PROJECT_DIR = Path(__file__).resolve().parent
DERIVED_DIR = PROJECT_DIR / "data" / "derived"
FIGURES_DIR = PROJECT_DIR / "figures"
SERIES_PATH = DERIVED_DIR / "rolling_12_month_mean_temperature.csv"
SUMMARY_PATH = DERIVED_DIR / "summary.json"
STANDARD_BASENAME = FIGURES_DIR / "wales_rolling_12_month_temperature_line_chart"
DARK_BASENAME = FIGURES_DIR / "wales_rolling_12_month_temperature_line_chart_square_dark"
OUTPUT_CSV = DERIVED_DIR / "wales_rolling_12_month_temperature_line_chart.csv"
TREND_BANDWIDTH_YEARS = 7.0


def _end_year_fraction(frame: pd.DataFrame) -> pd.Series:
    end_month = pd.to_datetime(frame["end_month"])
    return end_month.dt.year + (end_month.dt.month / 12.0)


def prepare_chart_data(series: pd.DataFrame, summary: dict[str, object]) -> tuple[pd.DataFrame, dict[str, float | str]]:
    chart = series.copy()
    chart["end_x"] = _end_year_fraction(chart)
    years = chart["end_x"].to_numpy(dtype=float)
    values = chart["mean_temperature_c"].to_numpy(dtype=float)
    chart["smoothed_trend_c"] = gaussian_smooth(years, values, TREND_BANDWIDTH_YEARS)
    published = chart[chart["status"] == "published-inputs"]
    if published.empty:
        raise ValueError("No published rolling windows found")
    latest = chart.iloc[-1]
    metadata: dict[str, float | str] = {
        "reference_mean_c": float(summary["derived_reference_1991_2020_c"]),
        "lowest_published_c": float(published["mean_temperature_c"].min()),
        "highest_published_c": float(published["mean_temperature_c"].max()),
        "latest_c": float(latest["mean_temperature_c"]),
        "latest_status": (
            "published inputs"
            if latest["status"] == "published-inputs"
            else "illustrative scenario"
        ),
        "latest_period_label": str(latest["period_label"]),
        "source_last_updated": str(summary["source_last_updated"]),
        "last_published_month": str(summary["last_published_month"]),
    }
    return chart, metadata


def render_standard(chart: pd.DataFrame, metadata: dict[str, float | str], basename: Path = STANDARD_BASENAME) -> tuple[Path, Path]:
    sns.set_theme(style="whitegrid", context="talk", palette="deep")
    plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none"})
    palette = sns.color_palette("deep", 10)
    value_colour = palette[0]
    reference_colour = palette[6]
    highest_colour = palette[3]
    trend_colour = "#1f2937"
    latest_colour = "#8a5a00"

    years = chart["end_x"].to_numpy(dtype=float)
    values = chart["mean_temperature_c"].to_numpy(dtype=float)
    trend = chart["smoothed_trend_c"].to_numpy(dtype=float)
    latest = float(metadata["latest_c"])
    latest_x = float(years[-1])

    fig, ax = plt.subplots(figsize=(STANDARD_WIDTH_PX / LINE_CHART_DPI, STANDARD_HEIGHT_PX / LINE_CHART_DPI), dpi=LINE_CHART_DPI)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.plot(years, values, color=value_colour, linewidth=2.0, marker="o", markersize=2.4, markeredgewidth=0, zorder=4)
    ax.plot(years, trend, color=trend_colour, linewidth=2.7, linestyle="--", zorder=5)
    ax.axhline(float(metadata["reference_mean_c"]), color=reference_colour, linewidth=2.4, zorder=2)
    ax.axhline(float(metadata["lowest_published_c"]), color=value_colour, linewidth=2.3, linestyle=(0, (8, 6)), zorder=2)
    ax.axhline(float(metadata["highest_published_c"]), color=highest_colour, linewidth=2.3, linestyle=(0, (8, 6)), zorder=2)
    ax.axhline(latest, color=latest_colour, linewidth=2.3, zorder=2)
    ax.scatter([latest_x], [latest], s=90, color=latest_colour, edgecolor="white", linewidth=1.2, zorder=7)
    ax.annotate(
        f"{metadata['latest_period_label']}: {latest:.2f}°C\n{metadata['latest_status']}",
        xy=(latest_x, latest),
        xytext=(-18, -56),
        textcoords="offset points",
        ha="right",
        va="top",
        fontsize=11,
        fontweight="bold",
        color=latest_colour,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": latest_colour, "alpha": 0.97},
        arrowprops={"arrowstyle": "-", "color": latest_colour, "linewidth": 1.1},
        zorder=8,
    )
    y_min = np.floor((min(float(metadata["lowest_published_c"]), values.min()) - 0.15) * 2) / 2
    y_max = np.ceil((max(latest, float(metadata["highest_published_c"]), values.max()) + 0.15) * 2) / 2
    ax.set_ylim(y_min, y_max)
    ax.set_yticks(np.arange(y_min, y_max + 0.01, 0.5))
    ax.set_xlim(float(years[0]) - 1, latest_x + 1)
    ax.set_xlabel("Window end (year)", fontsize=13, labelpad=12)
    ax.set_ylabel("Mean temperature (°C)", fontsize=14, labelpad=12)
    ax.set_title("WALES ROLLING 12-MONTH MEAN TEMPERATURE", fontsize=22, fontweight="bold", pad=24)
    ax.text(
        0.5,
        1.015,
        f"Complete monthly-start 12-month windows through {metadata['last_published_month']}",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=12.5,
    )
    ax.grid(True, linestyle=":", linewidth=1.0, color="#9aa5b1", alpha=0.85)
    ax.legend(
        handles=[
            Line2D([0], [0], color=reference_colour, lw=2.5, label="1991–2020 reference"),
            Line2D([0], [0], color=value_colour, lw=2.5, linestyle=(0, (8, 6)), label="lowest published window"),
            Line2D([0], [0], color=highest_colour, lw=2.5, linestyle=(0, (8, 6)), label="highest published window"),
            Line2D([0], [0], color=latest_colour, lw=2.5, label="latest window"),
            Line2D([0], [0], color=value_colour, marker="o", lw=2.0, markersize=4, label="window value"),
            Line2D([0], [0], color=trend_colour, lw=2.5, linestyle="--", label="smoothed trend"),
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.18),
        ncol=3,
        frameon=True,
        fontsize=10.5,
    )
    fig.text(0.065, 0.955, "Hinsawdd Cymru", ha="left", va="top", fontsize=13, fontweight="bold")
    fig.text(
        0.5,
        0.955,
        f"Source: Met Office Wales HadUK-Grid series, last updated {metadata['source_last_updated']}",
        ha="center",
        va="top",
        fontsize=10.5,
    )
    fig.text(0.935, 0.955, "Independent reproduction", ha="right", va="top", fontsize=10.5)
    fig.text(
        0.065,
        0.018,
        (
            "Each point is a complete monthly-start 12-month window. "
            f"Trend: Gaussian smoother, {TREND_BANDWIDTH_YEARS:g}-year bandwidth."
        ),
        ha="left",
        va="bottom",
        fontsize=9.2,
    )
    fig.subplots_adjust(left=0.08, right=0.975, top=0.84, bottom=0.28)
    return _save(fig, basename)


def render_dark(chart: pd.DataFrame, metadata: dict[str, float | str], basename: Path = DARK_BASENAME) -> tuple[Path, Path]:
    sns.set_theme(style="darkgrid", context="talk")
    plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none"})
    years = chart["end_x"].to_numpy(dtype=float)
    values = chart["mean_temperature_c"].to_numpy(dtype=float)
    trend = chart["smoothed_trend_c"].to_numpy(dtype=float)
    latest = float(metadata["latest_c"])
    latest_x = float(years[-1])
    published = chart[chart["status"] == "published-inputs"]
    prior = published.iloc[:-1]
    if prior.empty:
        raise ValueError("No prior published window for previous-high label")
    previous_row = prior.nlargest(1, "mean_temperature_c").iloc[0]
    previous = float(previous_row["mean_temperature_c"])
    previous_x = float(previous_row["end_x"])
    previous_label = str(previous_row["period_label"])

    fig, ax = plt.subplots(figsize=(SQUARE_PX / LINE_CHART_DPI, SQUARE_PX / LINE_CHART_DPI), dpi=LINE_CHART_DPI)
    fig.patch.set_facecolor(DARK_LINE_BACKGROUND)
    ax.set_facecolor(DARK_LINE_BACKGROUND)
    ax.plot(years, values, color=DARK_LINE_PERIOD_COLOUR, linewidth=1.8, alpha=0.95, zorder=3)
    ax.plot(years, trend, color=DARK_LINE_TREND_COLOUR, linewidth=4.0, zorder=4)
    ax.axhline(float(metadata["reference_mean_c"]), color=DARK_LINE_REFERENCE_COLOUR, linewidth=1.5, linestyle="--", alpha=0.9, zorder=2)
    ax.scatter([previous_x], [previous], s=70, color=DARK_LINE_PREVIOUS_HIGH, edgecolor=DARK_LINE_BACKGROUND, linewidth=0.8, zorder=6)
    ax.text(
        previous_x - 6,
        previous + 0.24,
        f"Previous high\n{previous_label}  {previous:.2f}°C",
        color=DARK_LINE_PREVIOUS_HIGH,
        fontsize=15,
        fontweight="bold",
        ha="right",
        va="bottom",
    )
    ax.scatter([latest_x], [latest], s=180, color=DARK_LINE_LATEST, edgecolor="white", linewidth=1.1, zorder=7)
    fig.text(0.07, 0.95, "WALES: ROLLING 12-MONTH", ha="left", va="top", fontsize=33, fontweight="bold", color=DARK_LINE_FOREGROUND)
    fig.text(0.07, 0.905, "MEAN TEMPERATURE", ha="left", va="top", fontsize=33, fontweight="bold", color=DARK_LINE_FOREGROUND)
    fig.text(
        0.07,
        0.855,
        f"Complete monthly-start windows through {metadata['last_published_month']}",
        ha="left",
        va="top",
        fontsize=18,
        color=DARK_LINE_MUTED,
    )
    fig.text(0.07, 0.782, f"{latest:.2f}°C", ha="left", va="top", fontsize=42, fontweight="bold", color=DARK_LINE_LATEST)
    fig.text(
        0.07,
        0.725,
        f"Latest window: {metadata['latest_period_label']}",
        ha="left",
        va="top",
        fontsize=21,
        color=DARK_LINE_FOREGROUND,
        fontweight="bold",
    )
    ax.set_position([0.11, 0.17, 0.84, 0.45])
    ax.set_xlim(float(years[0]) - 1, latest_x + 3)
    ax.set_ylim(6.75, 11.15)
    ax.set_ylabel("Mean temperature (°C)", color=DARK_LINE_FOREGROUND, fontsize=18, labelpad=10)
    ax.set_xlabel("Window end (year)", color=DARK_LINE_FOREGROUND, fontsize=18, labelpad=10)
    ax.tick_params(axis="x", colors=DARK_LINE_MUTED, labelsize=15)
    ax.tick_params(axis="y", colors=DARK_LINE_MUTED, labelsize=14)
    ax.grid(True, color=DARK_LINE_GRID, linewidth=1.2, alpha=0.6)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(DARK_LINE_FRAME)
    ax.spines[["left", "bottom"]].set_linewidth(2)
    legend = ax.legend(
        handles=[
            Line2D([0], [0], color=DARK_LINE_PERIOD_COLOUR, lw=2.2, label=LABEL_ROLLING_WINDOWS),
            Line2D([0], [0], color=DARK_LINE_TREND_COLOUR, lw=3.8, label="Smoothed historical trend"),
            Line2D([0], [0], color=DARK_LINE_REFERENCE_COLOUR, lw=1.8, linestyle="--", label=LABEL_REFERENCE_1991_2020),
        ],
        loc="lower right",
        frameon=True,
        facecolor=DARK_LINE_BACKGROUND,
        edgecolor=DARK_LINE_FRAME,
        fontsize=14,
    )
    for text in legend.get_texts():
        text.set_color(DARK_LINE_FOREGROUND)
    fig.text(
        0.07,
        0.082,
        "Source: Met Office Wales monthly HadUK-Grid areal series. Monthly means weighted by calendar days.",
        ha="left",
        va="bottom",
        fontsize=12.4,
        color=DARK_LINE_MUTED,
    )
    fig.text(0.07, 0.054, "Independent derived analysis: Hinsawdd Cymru.", ha="left", va="bottom", fontsize=12.4, color=DARK_LINE_MUTED)
    return _save(fig, basename)


def run(
    series_path: Path = SERIES_PATH,
    summary_path: Path = SUMMARY_PATH,
    standard_basename: Path = STANDARD_BASENAME,
    dark_basename: Path = DARK_BASENAME,
    output_csv: Path = OUTPUT_CSV,
) -> dict[str, Path]:
    series = pd.read_csv(series_path, parse_dates=["start_month", "end_month"])
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    chart, metadata = prepare_chart_data(series, summary)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    chart.to_csv(output_csv, index=False, float_format="%.6f")
    standard_png, standard_svg = render_standard(chart, metadata, standard_basename)
    dark_png, dark_svg = render_dark(chart, metadata, dark_basename)
    return {
        "standard_png": standard_png,
        "standard_svg": standard_svg,
        "dark_png": dark_png,
        "dark_svg": dark_svg,
        "data_csv": output_csv,
    }


if __name__ == "__main__":
    outputs = run()
    for name, path in outputs.items():
        print(f"{name}: {path}")
