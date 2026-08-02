"""Render light Seaborn and square dark-mode Project 001 line charts."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D

from equivalent_period_chart import load_inputs, prepare_chart_data

PROJECT_DIR = Path(__file__).resolve().parent
REPOSITORY_DIR = PROJECT_DIR.parents[1]
DERIVED_DIR = PROJECT_DIR / "data/derived"
FIGURES_DIR = PROJECT_DIR / "figures"
SOURCE_CSV = DERIVED_DIR / "august_to_july_mean_temperature.csv"
SUMMARY_JSON = DERIVED_DIR / "summary.json"
STANDARD_BASENAME = FIGURES_DIR / "wales_august_to_july_mean_temperature_line_chart"
DARK_BASENAME = FIGURES_DIR / "wales_august_to_july_mean_temperature_line_chart_square_dark"
OUTPUT_CSV = DERIVED_DIR / "wales_august_to_july_temperature_line_chart.csv"
ROOT_README = REPOSITORY_DIR / "README.md"
PROJECT_README = PROJECT_DIR / "README.md"

WIDTH_PX = 1600
HEIGHT_PX = 900
SQUARE_PX = 1080
DPI = 100
TREND_BANDWIDTH_YEARS = 7.0
ROOT_START = "<!-- BEGIN PROJECT 001 CHART PREVIEWS -->"
ROOT_END = "<!-- END PROJECT 001 CHART PREVIEWS -->"
PROJECT_START = "<!-- BEGIN LINE CHART PREVIEWS -->"
PROJECT_END = "<!-- END LINE CHART PREVIEWS -->"


@dataclass(frozen=True)
class VariantOutputs:
    standard_png: Path
    standard_svg: Path
    dark_png: Path
    dark_svg: Path
    data_csv: Path


def _save(fig: plt.Figure, basename: Path) -> tuple[Path, Path]:
    basename.parent.mkdir(parents=True, exist_ok=True)
    png = basename.with_suffix(".png")
    svg = basename.with_suffix(".svg")
    fig.savefig(png, dpi=DPI, facecolor=fig.get_facecolor())
    fig.savefig(svg, facecolor=fig.get_facecolor())
    plt.close(fig)
    return png, svg


def render_standard(
    chart: pd.DataFrame,
    metadata: dict[str, float | str],
    basename: Path = STANDARD_BASENAME,
) -> tuple[Path, Path]:
    """Render a 1600 x 900 light Seaborn presentation."""

    sns.set_theme(style="whitegrid", context="talk", palette="deep")
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "svg.fonttype": "none",
            "axes.edgecolor": "#4b5563",
            "axes.linewidth": 1.2,
        }
    )
    palette = sns.color_palette("deep", 10)
    value_colour = palette[0]
    reference_colour = palette[6]
    highest_colour = palette[3]
    trend_colour = "#1f2937"
    latest_colour = "#8a5a00"

    years = chart["end_year"].to_numpy(dtype=int)
    values = chart["mean_temperature_c"].to_numpy(dtype=float)
    trend = chart["smoothed_trend_c"].to_numpy(dtype=float)
    reference = float(metadata["reference_mean_c"])
    lowest = float(metadata["lowest_published_c"])
    highest = float(metadata["highest_published_c"])
    latest = float(metadata["latest_c"])
    latest_year = int(years[-1])

    fig, ax = plt.subplots(figsize=(WIDTH_PX / DPI, HEIGHT_PX / DPI), dpi=DPI)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.plot(
        years,
        values,
        color=value_colour,
        linewidth=2.0,
        marker="o",
        markersize=3.6,
        markeredgewidth=0,
        zorder=4,
    )
    ax.plot(years, trend, color=trend_colour, linewidth=2.7, linestyle="--", zorder=5)
    ax.axhline(reference, color=reference_colour, linewidth=2.4, zorder=2)
    ax.axhline(lowest, color=value_colour, linewidth=2.3, linestyle=(0, (8, 6)), zorder=2)
    ax.axhline(highest, color=highest_colour, linewidth=2.3, linestyle=(0, (8, 6)), zorder=2)
    ax.axhline(latest, color=latest_colour, linewidth=2.3, zorder=2)
    ax.scatter([latest_year], [latest], s=90, color=latest_colour, edgecolor="white", linewidth=1.2, zorder=7)
    ax.annotate(
        f"2025–26: {latest:.2f}°C\n{metadata['latest_status']}",
        xy=(latest_year, latest),
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

    y_min = np.floor((min(lowest, values.min()) - 0.15) * 2) / 2
    y_max = np.ceil((max(latest, highest, values.max()) + 0.15) * 2) / 2
    ax.set_ylim(y_min, y_max)
    ax.set_yticks(np.arange(y_min, y_max + 0.01, 0.5))
    ax.set_xlim(int(years[0]) - 1, latest_year + 1)
    ticks = [year for year in range(1890, 2030, 10) if years[0] <= year <= latest_year]
    if latest_year not in ticks:
        ticks.append(latest_year)
    ax.set_xticks(ticks)
    ax.tick_params(axis="x", rotation=90, labelsize=10)
    ax.tick_params(axis="y", labelsize=11)
    ax.set_xlabel("Period end year", fontsize=13, labelpad=12)
    ax.set_ylabel("Mean temperature (°C)", fontsize=14, labelpad=12)
    ax.set_title("WALES AUGUST–JULY MEAN TEMPERATURE", fontsize=22, fontweight="bold", pad=24)
    ax.text(
        0.5,
        1.015,
        "Complete twelve-month periods, 1884–85 to 2025–26",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=12.5,
    )
    ax.grid(True, linestyle=":", linewidth=1.0, color="#9aa5b1", alpha=0.85)
    ax.legend(
        handles=[
            Line2D([0], [0], color=reference_colour, lw=2.5, label="1991–2020 equivalent-period reference"),
            Line2D([0], [0], color=value_colour, lw=2.5, linestyle=(0, (8, 6)), label="lowest published period"),
            Line2D([0], [0], color=highest_colour, lw=2.5, linestyle=(0, (8, 6)), label="highest published period"),
            Line2D([0], [0], color=latest_colour, lw=2.5, label="latest 2025–26"),
            Line2D([0], [0], color=value_colour, marker="o", lw=2.0, markersize=4, label="period value"),
            Line2D([0], [0], color=trend_colour, lw=2.5, linestyle="--", label="smoothed trend"),
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.18),
        ncol=3,
        frameon=True,
        fontsize=10.5,
        columnspacing=1.6,
        handlelength=3.0,
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
            "Annual boundary shifted to August–July. "
            f"July 2026 = {float(metadata['july_2026_value_c']):.1f}°C illustrative scenario, "
            "not a published Met Office value. Trend: Gaussian smoother, 7-year bandwidth."
        ),
        ha="left",
        va="bottom",
        fontsize=9.2,
    )
    fig.subplots_adjust(left=0.08, right=0.975, top=0.84, bottom=0.28)
    return _save(fig, basename)


def render_dark(
    chart: pd.DataFrame,
    metadata: dict[str, float | str],
    basename: Path = DARK_BASENAME,
) -> tuple[Path, Path]:
    """Render a 1080 x 1080 dark-mode social presentation."""

    sns.set_theme(style="darkgrid", context="talk")
    plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none"})
    background = "#040914"
    foreground = "#e5e7eb"
    muted = "#a9b1bf"
    grid = "#334155"
    period_colour = "#cc3a53"
    trend_colour = "#32d3e2"
    reference_colour = "#94a3b8"
    previous_colour = "#f2c94c"
    latest_colour = "#ff5a67"
    frame = "#2b3445"

    years = chart["end_year"].to_numpy(dtype=int)
    values = chart["mean_temperature_c"].to_numpy(dtype=float)
    trend = chart["smoothed_trend_c"].to_numpy(dtype=float)
    latest = float(metadata["latest_c"])
    latest_year = int(years[-1])
    published = chart[chart["status"] == "published-inputs"]
    if published.empty:
        raise ValueError("No published-input periods found")
    previous_row = published.nlargest(1, "mean_temperature_c").iloc[0]
    previous = float(previous_row["mean_temperature_c"])
    previous_year = int(previous_row["end_year"])

    fig, ax = plt.subplots(figsize=(SQUARE_PX / DPI, SQUARE_PX / DPI), dpi=DPI)
    fig.patch.set_facecolor(background)
    ax.set_facecolor(background)
    ax.plot(years, values, color=period_colour, linewidth=1.8, alpha=0.95, zorder=3)
    ax.plot(years, trend, color=trend_colour, linewidth=4.0, zorder=4)
    ax.axhline(float(metadata["reference_mean_c"]), color=reference_colour, linewidth=1.5, linestyle="--", alpha=0.9, zorder=2)
    ax.scatter([previous_year], [previous], s=70, color=previous_colour, edgecolor=background, linewidth=0.8, zorder=6)
    ax.text(
        previous_year - 6,
        previous + 0.24,
        f"Previous high\n2006–07  {previous:.2f}°C",
        color=previous_colour,
        fontsize=15,
        fontweight="bold",
        ha="right",
        va="bottom",
    )
    ax.scatter([latest_year], [latest], s=180, color=latest_colour, edgecolor="white", linewidth=1.1, zorder=7)
    ax.text(2024.0, 10.74, f"2025–26 illustrative\n{latest:.2f}°C", color=foreground, fontsize=16, fontweight="bold", ha="right", va="bottom")

    fig.text(0.07, 0.95, "WALES: AUGUST–JULY", ha="left", va="top", fontsize=33, fontweight="bold", color=foreground)
    fig.text(0.07, 0.905, "MEAN TEMPERATURE", ha="left", va="top", fontsize=33, fontweight="bold", color=foreground)
    fig.text(0.07, 0.855, "Every equivalent 12-month period from 1884–85 to 2025–26", ha="left", va="top", fontsize=18, color=muted)
    fig.text(0.07, 0.782, f"{latest:.2f}°C", ha="left", va="top", fontsize=42, fontweight="bold", color=latest_colour)
    fig.text(0.07, 0.725, "2025–26 is the warmest equivalent period in the series", ha="left", va="top", fontsize=21, color=foreground, fontweight="bold")
    fig.text(0.07, 0.688, "Current point uses July 2026 at 18.0°C, shown as an illustrative scenario.", ha="left", va="top", fontsize=16.5, color=muted)

    ax.set_position([0.11, 0.17, 0.84, 0.45])
    ax.set_xlim(int(years[0]) - 1, latest_year + 3)
    ax.set_ylim(6.75, 11.15)
    ax.set_ylabel("Mean temperature (°C)", color=foreground, fontsize=18, labelpad=10)
    ax.set_xlabel("Period end year", color=foreground, fontsize=18, labelpad=10)
    ax.set_xticks([year for year in range(1890, 2030, 20) if years[0] <= year <= latest_year])
    ax.tick_params(axis="x", colors=muted, labelsize=15)
    ax.tick_params(axis="y", colors=muted, labelsize=14)
    ax.grid(True, color=grid, linewidth=1.2, alpha=0.6)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(frame)
    ax.spines[["left", "bottom"]].set_linewidth(2)
    legend = ax.legend(
        handles=[
            Line2D([0], [0], color=period_colour, lw=2.2, label="Individual August-to-July periods"),
            Line2D([0], [0], color=trend_colour, lw=3.8, label="Smoothed historical trend"),
            Line2D([0], [0], color=reference_colour, lw=1.8, linestyle="--", label="Derived 1991–2020 reference"),
        ],
        loc="lower right",
        frameon=True,
        facecolor=background,
        edgecolor=frame,
        fontsize=14,
    )
    for text in legend.get_texts():
        text.set_color(foreground)
    fig.text(0.07, 0.082, "Source: Met Office Wales monthly HadUK-Grid areal series. Monthly means weighted by calendar days.", ha="left", va="bottom", fontsize=12.4, color=muted)
    fig.text(0.07, 0.054, "Independent derived analysis: Hinsawdd Cymru.", ha="left", va="bottom", fontsize=12.4, color=muted)
    fig.text(0.07, 0.031, "July 2026 remains provisional and is shown as an illustrative scenario only.", ha="left", va="bottom", fontsize=12.4, color=muted)
    return _save(fig, basename)


def _marked(text: str, start: str, end: str, block: str, anchor: str) -> str:
    generated = f"{start}\n{block.strip()}\n{end}"
    if start in text or end in text:
        if text.count(start) != 1 or text.count(end) != 1:
            raise ValueError("README preview markers are incomplete or duplicated")
        before, rest = text.split(start, 1)
        _, after = rest.split(end, 1)
        return before + generated + after
    if anchor not in text:
        raise ValueError(f"README insertion anchor not found: {anchor}")
    return text.replace(anchor, generated + "\n\n" + anchor, 1)


def _migrate(text: str, old: str, new: str) -> str:
    if new in text:
        return text
    if old in text:
        return text.replace(old, new, 1)
    raise ValueError("Expected README documentation text was not found")


def update_readmes(root: Path = ROOT_README, project: Path = PROJECT_README) -> None:
    """Add both previews and reproduction references to the two public READMEs."""

    root_block = """## Project 001 visual summary

The standard line chart reproduces the conventional historical-series view with complete August-to-July periods. The square dark-mode version presents the same validated data for compact viewing.

<a href="projects/001-rolling-temperature/figures/wales_august_to_july_mean_temperature_line_chart.png"><img src="projects/001-rolling-temperature/figures/wales_august_to_july_mean_temperature_line_chart.png" alt="Wales August-to-July mean-temperature line chart" width="100%"></a>

<p align="center"><a href="projects/001-rolling-temperature/figures/wales_august_to_july_mean_temperature_line_chart_square_dark.png"><img src="projects/001-rolling-temperature/figures/wales_august_to_july_mean_temperature_line_chart_square_dark.png" alt="Square dark-mode Wales August-to-July mean-temperature line chart" width="72%"></a></p>

The final 2025–26 point remains provisional because July 2026 is represented by a clearly labelled illustrative scenario until the official Met Office Wales monthly value is published. [Read the full Project 001 report](projects/001-rolling-temperature/)."""
    project_block = """## Reproduced line-chart views

The following charts show the same validated August-to-July series in two presentation formats. Both use the calendar-day-weighted values produced by `analysis.py`; neither introduces a second temperature calculation.

### Standard light view

<a href="figures/wales_august_to_july_mean_temperature_line_chart.png"><img src="figures/wales_august_to_july_mean_temperature_line_chart.png" alt="Wales August-to-July mean-temperature line chart" width="100%"></a>

[Open the standard chart as SVG](figures/wales_august_to_july_mean_temperature_line_chart.svg)

### Square dark-mode view

<p align="center"><a href="figures/wales_august_to_july_mean_temperature_line_chart_square_dark.png"><img src="figures/wales_august_to_july_mean_temperature_line_chart_square_dark.png" alt="Square dark-mode Wales August-to-July mean-temperature line chart" width="78%"></a></p>

[Open the dark-mode chart as SVG](figures/wales_august_to_july_mean_temperature_line_chart_square_dark.svg)

Both views show 2025–26 as an illustrative scenario because the retained official Met Office source still ends in June 2026. Full presentation notes are in [`TEMPERATURE_LINE_CHART.md`](TEMPERATURE_LINE_CHART.md)."""

    root_text = _marked(root.read_text(encoding="utf-8"), ROOT_START, ROOT_END, root_block, "## Repository structure")
    root_text = _migrate(
        root_text,
        "python projects/001-rolling-temperature/analysis.py\npytest",
        "python projects/001-rolling-temperature/analysis.py\npython projects/001-rolling-temperature/line_chart_variants.py --update-readmes\npytest",
    )

    project_text = _marked(project.read_text(encoding="utf-8"), PROJECT_START, PROJECT_END, project_block, "## Historical trend since records began")
    project_text = _migrate(
        project_text,
        "python projects/001-rolling-temperature/august_to_july_stripes.py\npytest",
        "python projects/001-rolling-temperature/august_to_july_stripes.py\npython projects/001-rolling-temperature/line_chart_variants.py --update-readmes\npytest",
    )
    project_text = _migrate(
        project_text,
        "`analysis.py` performs the scientific calculation and produces the original full-width report figure. The presentation modules read validated derived outputs without introducing a second scientific method: `social_chart.py` produces the square dark chart, `warming_stripes.py` retains the calendar-year stripes and bars, and `august_to_july_stripes.py` produces the additional complete August-to-July stripes and bars documented in [`WARMING_STRIPES.md`](WARMING_STRIPES.md).",
        "`analysis.py` performs the scientific calculation and produces the original full-width report figure. The presentation modules read validated derived outputs without introducing a second scientific method: `social_chart.py` produces the original square dark chart, `warming_stripes.py` retains the calendar-year stripes and bars, `august_to_july_stripes.py` produces the additional complete August-to-July stripes and bars, and `line_chart_variants.py` produces the standard and square dark-mode line-chart views.",
    )
    project_text = _migrate(
        project_text,
        "- [`august_to_july_stripes.py`](august_to_july_stripes.py), additional August-to-July stripes and temperature bars\n- [`WARMING_STRIPES.md`](WARMING_STRIPES.md), full-width previews and interpretation for both annual boundaries",
        "- [`august_to_july_stripes.py`](august_to_july_stripes.py), additional August-to-July stripes and temperature bars\n- [`line_chart_variants.py`](line_chart_variants.py), standard and square dark-mode August-to-July line charts\n- [`TEMPERATURE_LINE_CHART.md`](TEMPERATURE_LINE_CHART.md), line-chart interpretation and reproduction notes\n- [`WARMING_STRIPES.md`](WARMING_STRIPES.md), full-width previews and interpretation for both annual boundaries",
    )
    project_text = _migrate(
        project_text,
        "- [`data/derived/wales_august_to_july_warming_stripes.csv`](data/derived/wales_august_to_july_warming_stripes.csv), August-to-July reference, anomalies and published/provisional status used by the new graphics\n- [`data/derived/independent_verification.json`]",
        "- [`data/derived/wales_august_to_july_warming_stripes.csv`](data/derived/wales_august_to_july_warming_stripes.csv), August-to-July reference, anomalies and published/provisional status used by the new graphics\n- [`data/derived/wales_august_to_july_temperature_line_chart.csv`](data/derived/wales_august_to_july_temperature_line_chart.csv), presentation data and descriptive smoothed trend used by both line-chart variants\n- [`data/derived/independent_verification.json`]",
    )
    project_text = _migrate(
        project_text,
        "Calendar-year and August-to-July warming stripes and temperature bars:",
        "Standard and square dark-mode August-to-July line charts:\n\n- `figures/wales_august_to_july_mean_temperature_line_chart.{png,svg}`\n- `figures/wales_august_to_july_mean_temperature_line_chart_square_dark.{png,svg}`\n- [`TEMPERATURE_LINE_CHART.md`](TEMPERATURE_LINE_CHART.md), full previews and interpretation\n\nCalendar-year and August-to-July warming stripes and temperature bars:",
    )
    root.write_text(root_text, encoding="utf-8")
    project.write_text(project_text, encoding="utf-8")


def run(
    source_csv: Path = SOURCE_CSV,
    summary_json: Path = SUMMARY_JSON,
    standard_basename: Path = STANDARD_BASENAME,
    dark_basename: Path = DARK_BASENAME,
    output_csv: Path = OUTPUT_CSV,
    *,
    update_documentation: bool = False,
) -> VariantOutputs:
    data, summary = load_inputs(source_csv, summary_json)
    chart, metadata = prepare_chart_data(data, summary)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    chart.to_csv(output_csv, index=False, float_format="%.6f")
    standard_png, standard_svg = render_standard(chart, metadata, standard_basename)
    dark_png, dark_svg = render_dark(chart, metadata, dark_basename)
    if update_documentation:
        update_readmes()
    return VariantOutputs(standard_png, standard_svg, dark_png, dark_svg, output_csv)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-csv", type=Path, default=SOURCE_CSV)
    parser.add_argument("--summary-json", type=Path, default=SUMMARY_JSON)
    parser.add_argument("--standard-basename", type=Path, default=STANDARD_BASENAME)
    parser.add_argument("--dark-basename", type=Path, default=DARK_BASENAME)
    parser.add_argument("--output-csv", type=Path, default=OUTPUT_CSV)
    parser.add_argument("--update-readmes", action="store_true")
    args = parser.parse_args()
    outputs = run(
        source_csv=args.source_csv,
        summary_json=args.summary_json,
        standard_basename=args.standard_basename,
        dark_basename=args.dark_basename,
        output_csv=args.output_csv,
        update_documentation=args.update_readmes,
    )
    for name, path in outputs.__dict__.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
