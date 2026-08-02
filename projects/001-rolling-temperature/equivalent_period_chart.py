"""Render a Met Office-inspired Wales August-to-July temperature line chart.

This presentation module reads the validated Project 001 derived series. It does
not recalculate monthly or annual temperatures and never writes to the retained
official raw-source snapshot.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D

PROJECT_DIR = Path(__file__).resolve().parent
DERIVED_DIR = PROJECT_DIR / "data/derived"
FIGURES_DIR = PROJECT_DIR / "figures"
SOURCE_CSV = DERIVED_DIR / "august_to_july_mean_temperature.csv"
SUMMARY_JSON = DERIVED_DIR / "summary.json"
OUTPUT_BASENAME = FIGURES_DIR / "wales_august_to_july_mean_temperature_line_chart"
OUTPUT_CSV = DERIVED_DIR / "wales_august_to_july_temperature_line_chart.csv"

WIDTH_PX = 1600
HEIGHT_PX = 900
DPI = 100
REFERENCE_START_END_YEAR = 1991
REFERENCE_END_END_YEAR = 2020
TREND_BANDWIDTH_YEARS = 7.0

VALUE_COLOUR = "#101a66"
TREND_COLOUR = "#111111"
REFERENCE_COLOUR = "#d85ac8"
LOWEST_COLOUR = "#2c67b1"
HIGHEST_COLOUR = "#d84a43"
LATEST_COLOUR = "#7a5316"
GRID_COLOUR = "#8f8f8f"

REQUIRED_COLUMNS = {
    "period",
    "start_date",
    "end_date",
    "end_year",
    "mean_temperature_c",
    "status",
}


def load_inputs(
    source_csv: Path = SOURCE_CSV,
    summary_json: Path = SUMMARY_JSON,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Load and validate the existing August-to-July derived outputs."""

    if not source_csv.exists():
        raise FileNotFoundError(
            f"Missing {source_csv}. Run analysis.py before rendering the chart."
        )
    if not summary_json.exists():
        raise FileNotFoundError(
            f"Missing {summary_json}. Run analysis.py before rendering the chart."
        )

    data = pd.read_csv(source_csv)
    missing = REQUIRED_COLUMNS.difference(data.columns)
    if missing:
        raise ValueError(f"Derived series is missing columns: {sorted(missing)}")
    if data.empty:
        raise ValueError("Derived August-to-July series is empty")
    if data["end_year"].duplicated().any():
        raise ValueError("August-to-July period end years must be unique")

    data = data.sort_values("end_year").reset_index(drop=True)
    expected = np.arange(int(data.end_year.iloc[0]), int(data.end_year.iloc[-1]) + 1)
    if not np.array_equal(data["end_year"].to_numpy(dtype=int), expected):
        raise ValueError("August-to-July periods must be continuous")
    if str(data.iloc[0]["period"]) != "1884-08 to 1885-07":
        raise ValueError("Expected the first complete period to be 1884-08 to 1885-07")
    if str(data.iloc[-1]["period"]) != "2025-08 to 2026-07":
        raise ValueError("Expected the final period to be 2025-08 to 2026-07")

    summary = json.loads(summary_json.read_text(encoding="utf-8"))
    return data, summary


def gaussian_smooth(
    years: np.ndarray,
    values: np.ndarray,
    bandwidth_years: float = TREND_BANDWIDTH_YEARS,
) -> np.ndarray:
    """Return a deterministic Gaussian-kernel smoother for presentation."""

    if bandwidth_years <= 0:
        raise ValueError("Trend bandwidth must be positive")
    if len(years) != len(values) or len(years) < 2:
        raise ValueError("Trend inputs must contain matching multi-year sequences")
    if not np.isfinite(years).all() or not np.isfinite(values).all():
        raise ValueError("Trend inputs must be finite")

    distances = years[:, None] - years[None, :]
    weights = np.exp(-0.5 * (distances / bandwidth_years) ** 2)
    return (weights @ values) / weights.sum(axis=1)


def prepare_chart_data(
    data: pd.DataFrame,
    summary: dict[str, object],
) -> tuple[pd.DataFrame, dict[str, float | str]]:
    """Add trend and chart-reference values without changing the science."""

    chart = data.copy()
    years = chart["end_year"].to_numpy(dtype=float)
    values = chart["mean_temperature_c"].to_numpy(dtype=float)
    chart["smoothed_trend_c"] = gaussian_smooth(years, values)

    reference_mask = chart["end_year"].between(
        REFERENCE_START_END_YEAR,
        REFERENCE_END_END_YEAR,
    )
    if int(reference_mask.sum()) != 30:
        raise ValueError("Expected 30 August-to-July periods in the 1991-2020 reference")
    reference_mean = float(chart.loc[reference_mask, "mean_temperature_c"].mean())

    published = chart[chart["status"] == "published-inputs"]
    if published.empty:
        raise ValueError("No published-input periods found")

    latest = chart.iloc[-1]
    status = str(latest["status"])
    status_label = (
        "published inputs"
        if status == "published-inputs"
        else "illustrative scenario"
    )
    values_meta: dict[str, float | str] = {
        "reference_mean_c": reference_mean,
        "lowest_published_c": float(published["mean_temperature_c"].min()),
        "highest_published_c": float(published["mean_temperature_c"].max()),
        "latest_c": float(latest["mean_temperature_c"]),
        "latest_status": status_label,
        "july_2026_value_c": float(summary["july_2026_value_used_c"]),
        "source_last_updated": str(summary["source_last_updated"]),
    }

    for key, value in values_meta.items():
        chart[key] = value
    return chart, values_meta


def render_chart(
    chart: pd.DataFrame,
    metadata: dict[str, float | str],
    output_basename: Path = OUTPUT_BASENAME,
) -> tuple[Path, Path]:
    """Render the 1600 x 900 PNG and matching SVG chart."""

    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "svg.fonttype": "none",
            "axes.edgecolor": "#444444",
            "axes.linewidth": 1.2,
        }
    )

    fig, ax = plt.subplots(figsize=(WIDTH_PX / DPI, HEIGHT_PX / DPI), dpi=DPI)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    years = chart["end_year"].to_numpy(dtype=int)
    temperatures = chart["mean_temperature_c"].to_numpy(dtype=float)
    trend = chart["smoothed_trend_c"].to_numpy(dtype=float)

    ax.plot(
        years,
        temperatures,
        color=VALUE_COLOUR,
        linewidth=2.1,
        marker="o",
        markersize=3.8,
        markerfacecolor=VALUE_COLOUR,
        markeredgewidth=0,
        zorder=4,
    )
    ax.plot(
        years,
        trend,
        color=TREND_COLOUR,
        linewidth=2.6,
        linestyle="--",
        zorder=5,
    )

    reference = float(metadata["reference_mean_c"])
    lowest = float(metadata["lowest_published_c"])
    highest = float(metadata["highest_published_c"])
    latest = float(metadata["latest_c"])
    latest_status = str(metadata["latest_status"])
    july_value = float(metadata["july_2026_value_c"])
    source_last_updated = str(metadata["source_last_updated"])

    ax.axhline(reference, color=REFERENCE_COLOUR, linewidth=2.3, zorder=2)
    ax.axhline(lowest, color=LOWEST_COLOUR, linewidth=2.3, linestyle=(0, (9, 6)), zorder=2)
    ax.axhline(highest, color=HIGHEST_COLOUR, linewidth=2.3, linestyle=(0, (9, 6)), zorder=2)
    ax.axhline(latest, color=LATEST_COLOUR, linewidth=2.3, zorder=2)

    latest_year = int(years[-1])
    ax.scatter(
        [latest_year],
        [latest],
        s=92,
        color=LATEST_COLOUR,
        edgecolor="white",
        linewidth=1.2,
        zorder=7,
    )
    ax.annotate(
        f"2025–26: {latest:.2f}°C\n{latest_status}",
        xy=(latest_year, latest),
        xytext=(-16, -54),
        textcoords="offset points",
        ha="right",
        va="top",
        fontsize=11,
        fontweight="bold",
        color=LATEST_COLOUR,
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": "white",
            "edgecolor": LATEST_COLOUR,
            "alpha": 0.96,
        },
        arrowprops={"arrowstyle": "-", "color": LATEST_COLOUR, "linewidth": 1.1},
        zorder=8,
    )

    y_min = np.floor((min(lowest, temperatures.min()) - 0.15) * 2) / 2
    y_max = np.ceil((max(latest, highest, temperatures.max()) + 0.15) * 2) / 2
    ax.set_ylim(y_min, y_max)
    ax.set_yticks(np.arange(y_min, y_max + 0.01, 0.5))
    ax.set_xlim(int(years[0]) - 1, latest_year + 1)

    decade_ticks = list(range(1890, 2030, 10))
    decade_ticks = [year for year in decade_ticks if years[0] <= year <= latest_year]
    if latest_year not in decade_ticks:
        decade_ticks.append(latest_year)
    ax.set_xticks(decade_ticks)
    ax.tick_params(axis="x", rotation=90, labelsize=10)
    ax.tick_params(axis="y", labelsize=11)

    ax.set_xlabel("Period end year", fontsize=13, labelpad=12)
    ax.set_ylabel("Mean temperature (°C)", fontsize=14, labelpad=12)
    ax.set_title(
        "WALES AUGUST–JULY MEAN TEMPERATURE",
        fontsize=22,
        fontweight="bold",
        pad=24,
    )
    ax.text(
        0.5,
        1.015,
        "Complete twelve-month periods, 1884–85 to 2025–26",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=12.5,
    )

    ax.grid(True, which="major", linestyle=":", linewidth=1.0, color=GRID_COLOUR, alpha=0.72)
    ax.spines["top"].set_visible(True)
    ax.spines["right"].set_visible(True)

    legend_handles = [
        Line2D([0], [0], color=REFERENCE_COLOUR, lw=2.5, label="1991–2020 equivalent-period reference"),
        Line2D([0], [0], color=LOWEST_COLOUR, lw=2.5, linestyle=(0, (9, 6)), label="lowest published period"),
        Line2D([0], [0], color=HIGHEST_COLOUR, lw=2.5, linestyle=(0, (9, 6)), label="highest published period"),
        Line2D([0], [0], color=LATEST_COLOUR, lw=2.5, label="latest 2025–26"),
        Line2D([0], [0], color=VALUE_COLOUR, marker="o", lw=2.0, markersize=4, label="period value"),
        Line2D([0], [0], color=TREND_COLOUR, lw=2.5, linestyle="--", label="smoothed trend"),
    ]
    ax.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.18),
        ncol=3,
        frameon=True,
        fontsize=10.5,
        columnspacing=1.6,
        handlelength=3.0,
    )

    fig.text(
        0.065,
        0.955,
        "Hinsawdd Cymru",
        ha="left",
        va="top",
        fontsize=13,
        fontweight="bold",
    )
    fig.text(
        0.5,
        0.955,
        f"Source: Met Office Wales HadUK-Grid series, last updated {source_last_updated}",
        ha="center",
        va="top",
        fontsize=10.5,
    )
    fig.text(
        0.935,
        0.955,
        "Independent reproduction",
        ha="right",
        va="top",
        fontsize=10.5,
    )
    fig.text(
        0.065,
        0.018,
        (
            "Annual boundary shifted from January–December to August–July. "
            f"July 2026 = {july_value:.1f}°C illustrative scenario; "
            "not a published or endorsed Met Office value. "
            f"Trend: Gaussian smoother, {TREND_BANDWIDTH_YEARS:g}-year bandwidth."
        ),
        ha="left",
        va="bottom",
        fontsize=9.2,
    )

    fig.subplots_adjust(left=0.08, right=0.975, top=0.84, bottom=0.28)
    output_basename.parent.mkdir(parents=True, exist_ok=True)
    png_path = output_basename.with_suffix(".png")
    svg_path = output_basename.with_suffix(".svg")
    fig.savefig(png_path, dpi=DPI, facecolor="white")
    fig.savefig(svg_path, facecolor="white")
    plt.close(fig)
    return png_path, svg_path


def run(
    source_csv: Path = SOURCE_CSV,
    summary_json: Path = SUMMARY_JSON,
    output_basename: Path = OUTPUT_BASENAME,
    output_csv: Path = OUTPUT_CSV,
) -> dict[str, Path]:
    """Generate the chart, SVG and machine-readable presentation data."""

    data, summary = load_inputs(source_csv, summary_json)
    chart, metadata = prepare_chart_data(data, summary)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    chart.to_csv(output_csv, index=False, float_format="%.6f")
    png_path, svg_path = render_chart(chart, metadata, output_basename)
    return {"png": png_path, "svg": svg_path, "csv": output_csv}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-csv", type=Path, default=SOURCE_CSV)
    parser.add_argument("--summary-json", type=Path, default=SUMMARY_JSON)
    parser.add_argument("--output-basename", type=Path, default=OUTPUT_BASENAME)
    parser.add_argument("--output-csv", type=Path, default=OUTPUT_CSV)
    args = parser.parse_args()

    outputs = run(
        source_csv=args.source_csv,
        summary_json=args.summary_json,
        output_basename=args.output_basename,
        output_csv=args.output_csv,
    )
    for name, path in outputs.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
