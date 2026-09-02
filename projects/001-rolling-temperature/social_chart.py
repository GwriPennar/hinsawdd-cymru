"""Generate a square dark-mode Seaborn graphic for social sharing.

This module does not recalculate the climate result. It reads the derived
August-to-July series and summary produced by ``analysis.py`` and renders the
same values in a more legible 1:1 presentation.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

PROJECT_DIR = Path(__file__).resolve().parent
DERIVED_DIR = PROJECT_DIR / "data/derived"
FIGURES_DIR = PROJECT_DIR / "figures"
SERIES_PATH = DERIVED_DIR / "august_to_july_mean_temperature.csv"
SUMMARY_PATH = DERIVED_DIR / "summary.json"
OUTPUT_BASE = FIGURES_DIR / "wales_august_to_july_mean_temperature_square_dark"

BACKGROUND = "#090b10"
FOREGROUND = "#f5f7fa"
MUTED = "#aab2bd"
GRID = "#303641"
TEMPERATURE_RED = "#ff4d5a"
MOVING_AVERAGE_CYAN = "#45e0e5"
PREVIOUS_HIGH_AMBER = "#ffd166"
REFERENCE_GREY = "#89919c"


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

    sns.set_theme(
        style="darkgrid",
        context="talk",
        rc={
            "figure.facecolor": BACKGROUND,
            "axes.facecolor": BACKGROUND,
            "axes.edgecolor": MUTED,
            "axes.labelcolor": FOREGROUND,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "text.color": FOREGROUND,
            "grid.color": GRID,
            "grid.alpha": 0.55,
            "legend.facecolor": BACKGROUND,
            "legend.edgecolor": GRID,
            "font.family": "DejaVu Sans",
        },
    )
    plt.rcParams.update({"svg.fonttype": "none"})

    fig = plt.figure(figsize=(10.8, 10.8), dpi=100, facecolor=BACKGROUND)
    ax = fig.add_axes([0.11, 0.16, 0.84, 0.52], facecolor=BACKGROUND)

    sns.lineplot(
        data=data,
        x="end_year",
        y="mean_temperature_c",
        ax=ax,
        color=TEMPERATURE_RED,
        linewidth=1.7,
        alpha=0.58,
        label="Individual August-to-July periods",
        zorder=2,
    )
    sns.lineplot(
        data=data,
        x="end_year",
        y="trailing_10_period_mean_c",
        ax=ax,
        color=MOVING_AVERAGE_CYAN,
        linewidth=4.4,
        label="Trailing 10-year average",
        zorder=4,
    )

    ax.axhline(
        reference_1991_2020_c,
        color=REFERENCE_GREY,
        linestyle="--",
        linewidth=1.4,
        alpha=0.85,
        label="Derived 1991–2020 reference",
        zorder=1,
    )

    ax.scatter(
        [previous.end_year],
        [previous.mean_temperature_c],
        s=85,
        color=PREVIOUS_HIGH_AMBER,
        edgecolor=BACKGROUND,
        linewidth=1.5,
        zorder=6,
    )
    ax.scatter(
        [current.end_year],
        [current.mean_temperature_c],
        s=230,
        color=FOREGROUND,
        edgecolor=BACKGROUND,
        linewidth=1.5,
        zorder=7,
    )
    ax.scatter(
        [current.end_year],
        [current.mean_temperature_c],
        s=105,
        color=TEMPERATURE_RED,
        zorder=8,
    )

    ax.annotate(
        f"Previous high\n2006–07  {previous.mean_temperature_c:.2f}°C",
        (previous.end_year, previous.mean_temperature_c),
        xytext=(-10, 24),
        textcoords="offset points",
        ha="right",
        va="bottom",
        color=PREVIOUS_HIGH_AMBER,
        fontsize=11,
        fontweight="bold",
    )
    ax.annotate(
        f"2025–26 {current_kind}\n{current.mean_temperature_c:.2f}°C",
        (current.end_year, current.mean_temperature_c),
        xytext=(-12, 24),
        textcoords="offset points",
        ha="right",
        va="bottom",
        color=FOREGROUND,
        fontsize=12,
        fontweight="bold",
    )

    first_end_year = int(data["end_year"].min())
    last_end_year = int(data["end_year"].max())
    first_tick = ((first_end_year + 9) // 10) * 10
    ax.set_xticks(list(range(first_tick, last_end_year + 1, 20)))
    ax.set_xlim(first_end_year, last_end_year + 3)
    ax.set_ylim(
        float(data["mean_temperature_c"].min()) - 0.25,
        float(data["mean_temperature_c"].max()) + 0.55,
    )
    ax.set_xlabel("Period end year", fontsize=13, labelpad=12)
    ax.set_ylabel("Mean temperature (°C)", fontsize=13, labelpad=12)
    ax.tick_params(axis="both", labelsize=11)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRID)

    legend = ax.legend(
        loc="lower right",
        frameon=True,
        fontsize=10,
        borderpad=0.8,
        labelspacing=0.6,
    )
    legend.get_frame().set_alpha(0.85)
    for text in legend.get_texts():
        text.set_color(FOREGROUND)

    fig.text(
        0.07,
        0.93,
        "WALES: AUGUST–JULY MEAN TEMPERATURE",
        color=FOREGROUND,
        fontsize=24,
        fontweight="bold",
        ha="left",
        va="top",
    )
    fig.text(
        0.07,
        0.885,
        "Every equivalent 12-month period from 1884–85 to 2025–26",
        color=MUTED,
        fontsize=14,
        ha="left",
        va="top",
    )
    fig.text(
        0.07,
        0.81,
        f"{current.mean_temperature_c:.2f}°C",
        color=TEMPERATURE_RED,
        fontsize=44,
        fontweight="bold",
        ha="left",
        va="top",
    )
    fig.text(
        0.07,
        0.75,
        "2025–26 is the warmest equivalent period in the series",
        color=FOREGROUND,
        fontsize=16,
        fontweight="bold",
        ha="left",
        va="top",
    )
    fig.text(
        0.07,
        0.715,
        f"Current point uses July 2026 at {july_2026_c:.1f}°C ({july_kind}).",
        color=MUTED,
        fontsize=11.5,
        ha="left",
        va="top",
    )
    fig.text(
        0.07,
        0.08,
        "Source: Met Office Wales monthly HadUK-Grid areal series. Monthly means weighted by calendar days.",
        color=MUTED,
        fontsize=9.5,
        ha="left",
        va="bottom",
    )
    fig.text(
        0.07,
        0.05,
        "Independent derived analysis: Hinsawdd Cymru • github.com/GwriPennar/hinsawdd-cymru",
        color=MUTED,
        fontsize=9.5,
        ha="left",
        va="bottom",
    )

    output_base.parent.mkdir(parents=True, exist_ok=True)
    png_path = output_base.with_suffix(".png")
    svg_path = output_base.with_suffix(".svg")
    fig.savefig(png_path, dpi=100, facecolor=BACKGROUND)
    fig.savefig(svg_path, facecolor=BACKGROUND)
    plt.close(fig)
    return png_path, svg_path


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
        reference_1991_2020_c=float(summary["derived_reference_1991_2020_c"]),
    )
    print(json.dumps({"png": str(png_path), "svg": str(svg_path)}, indent=2))


if __name__ == "__main__":
    main()
