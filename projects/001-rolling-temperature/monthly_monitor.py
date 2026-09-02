"""Monthly rolling 12-month temperature monitor figures for Project 001."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from figure_style import (
    LABEL_REFERENCE_1991_2020,
    LABEL_ROLLING_AVERAGE,
    LABEL_ROLLING_WINDOWS,
    LIGHT_AVERAGE_COLOUR,
    LIGHT_PERIOD_COLOUR,
    LIGHT_REFERENCE_COLOUR,
    LIGHT_TREND_DPI,
    LIGHT_TREND_FIGSIZE,
    SOCIAL_AVERAGE_COLOUR,
    SOCIAL_BACKGROUND,
    SOCIAL_DPI,
    SOCIAL_FIGSIZE_INCHES,
    SOCIAL_FOREGROUND,
    SOCIAL_GRID,
    SOCIAL_MUTED,
    SOCIAL_PERIOD_COLOUR,
    SOCIAL_PREVIOUS_HIGH,
    SOCIAL_REFERENCE_COLOUR,
)

PROJECT_DIR = Path(__file__).resolve().parent
DERIVED_DIR = PROJECT_DIR / "data" / "derived"
FIGURES_DIR = PROJECT_DIR / "figures"
SERIES_PATH = DERIVED_DIR / "rolling_12_month_mean_temperature.csv"
SUMMARY_PATH = DERIVED_DIR / "summary.json"
HISTORY_BASENAME = FIGURES_DIR / "wales_rolling_12_month_temperature_history"
DARK_BASENAME = FIGURES_DIR / "wales_rolling_12_month_temperature_square_dark"
LATEST_GOLD = "#f4c430"


def _load() -> tuple[pd.DataFrame, dict]:
    series = pd.read_csv(SERIES_PATH, parse_dates=["start_month", "end_month"])
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    return series, summary


def _save(fig: plt.Figure, basename: Path, *, dpi: int, bbox_inches: str | None = None) -> tuple[Path, Path]:
    basename.parent.mkdir(parents=True, exist_ok=True)
    png = basename.with_suffix(".png")
    svg = basename.with_suffix(".svg")
    fig.savefig(png, dpi=dpi, facecolor=fig.get_facecolor(), bbox_inches=bbox_inches)
    fig.savefig(svg, facecolor=fig.get_facecolor(), bbox_inches=bbox_inches)
    plt.close(fig)
    return png, svg


def _end_year_fraction(frame: pd.DataFrame) -> pd.Series:
    return frame["end_month"].dt.year + (frame["end_month"].dt.month / 12.0)


def render_history(series: pd.DataFrame, summary: dict, basename: Path = HISTORY_BASENAME) -> tuple[Path, Path]:
    data = series.copy()
    data["end_x"] = _end_year_fraction(data)
    data["trailing_10_window_mean_c"] = data["mean_temperature_c"].rolling(10, min_periods=10).mean()
    current = data.iloc[-1]
    previous = data.iloc[:-1].nlargest(1, "mean_temperature_c").iloc[0]
    reference = float(summary["derived_reference_1991_2020_c"])

    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams.update({"svg.fonttype": "none"})
    fig, ax = plt.subplots(figsize=LIGHT_TREND_FIGSIZE)
    sns.lineplot(
        data=data,
        x="end_x",
        y="mean_temperature_c",
        ax=ax,
        color=LIGHT_PERIOD_COLOUR,
        linewidth=1.1,
        alpha=0.72,
        label=LABEL_ROLLING_WINDOWS,
        zorder=2,
    )
    sns.lineplot(
        data=data,
        x="end_x",
        y="trailing_10_window_mean_c",
        ax=ax,
        color=LIGHT_AVERAGE_COLOUR,
        linewidth=2.8,
        label=LABEL_ROLLING_AVERAGE,
        zorder=4,
    )
    ax.axhline(
        reference,
        linestyle=":",
        linewidth=1.1,
        color=LIGHT_REFERENCE_COLOUR,
        label=LABEL_REFERENCE_1991_2020,
        zorder=1,
    )
    prev_x = float(previous["end_x"])
    curr_x = float(current["end_x"])
    ax.scatter([prev_x], [previous.mean_temperature_c], s=45, color=SOCIAL_PREVIOUS_HIGH, zorder=5)
    ax.scatter([curr_x], [current.mean_temperature_c], s=70, color=LATEST_GOLD, zorder=6)
    period = summary["current_window"]["period_label"]
    ax.annotate(
        f"Previous high\n{previous['period_label']}: {previous.mean_temperature_c:.2f}°C",
        (prev_x, previous.mean_temperature_c),
        xytext=(-12, 18),
        textcoords="offset points",
        ha="right",
        fontsize=8,
    )
    ax.annotate(
        f"Latest\n{current.mean_temperature_c:.2f}°C",
        (curr_x, current.mean_temperature_c),
        xytext=(-10, 18),
        textcoords="offset points",
        ha="right",
        fontsize=8,
    )
    ax.set(
        title=f"Wales rolling 12-month mean temperature to {period}",
        xlabel="Window end (year)",
        ylabel="Mean temperature (°C)",
    )
    ax.set_xlim(float(data["end_x"].min()) - 0.5, float(data["end_x"].max()) + 0.5)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper left")
    fig.text(
        0.01,
        0.01,
        (
            "Source: Met Office Wales monthly HadUK-Grid areal series. "
            "Each point is a complete monthly-start 12-month window. "
            f"Latest window ends {summary['last_published_month']}."
        ),
        fontsize=7,
    )
    fig.tight_layout(rect=(0, 0.045, 1, 1))
    return _save(fig, basename, dpi=LIGHT_TREND_DPI, bbox_inches="tight")


def render_dark_square(series: pd.DataFrame, summary: dict, basename: Path = DARK_BASENAME) -> tuple[Path, Path]:
    data = series.copy()
    data["end_x"] = _end_year_fraction(data)
    data["trailing_10_window_mean_c"] = data["mean_temperature_c"].rolling(10, min_periods=10).mean()
    current = data.iloc[-1]
    previous = data.iloc[:-1].nlargest(1, "mean_temperature_c").iloc[0]
    reference = float(summary["derived_reference_1991_2020_c"])
    period = summary["current_window"]["period_label"]
    rank = int(summary["current_window"]["rank_warmest"])
    total = int(summary["current_window"]["window_count"])
    current_x = float(current["end_x"])
    previous_x = float(previous["end_x"])

    sns.set_theme(
        style="darkgrid",
        context="talk",
        rc={
            "figure.facecolor": SOCIAL_BACKGROUND,
            "axes.facecolor": SOCIAL_BACKGROUND,
            "axes.edgecolor": SOCIAL_MUTED,
            "axes.labelcolor": SOCIAL_FOREGROUND,
            "xtick.color": SOCIAL_MUTED,
            "ytick.color": SOCIAL_MUTED,
            "text.color": SOCIAL_FOREGROUND,
            "grid.color": SOCIAL_GRID,
            "grid.alpha": 0.55,
            "legend.facecolor": SOCIAL_BACKGROUND,
            "legend.edgecolor": SOCIAL_GRID,
            "font.family": "DejaVu Sans",
        },
    )
    plt.rcParams.update({"svg.fonttype": "none"})
    fig = plt.figure(figsize=SOCIAL_FIGSIZE_INCHES, dpi=SOCIAL_DPI, facecolor=SOCIAL_BACKGROUND)
    ax = fig.add_axes([0.11, 0.16, 0.84, 0.52], facecolor=SOCIAL_BACKGROUND)
    sns.lineplot(
        data=data,
        x="end_x",
        y="mean_temperature_c",
        ax=ax,
        linewidth=1.7,
        alpha=0.58,
        color=SOCIAL_PERIOD_COLOUR,
        label=LABEL_ROLLING_WINDOWS,
        zorder=2,
    )
    sns.lineplot(
        data=data,
        x="end_x",
        y="trailing_10_window_mean_c",
        ax=ax,
        linewidth=4.4,
        color=SOCIAL_AVERAGE_COLOUR,
        label=LABEL_ROLLING_AVERAGE,
        zorder=4,
    )
    ax.axhline(
        reference,
        linestyle="--",
        linewidth=1.4,
        color=SOCIAL_REFERENCE_COLOUR,
        alpha=0.85,
        label=LABEL_REFERENCE_1991_2020,
        zorder=1,
    )
    ax.scatter([previous_x], [previous.mean_temperature_c], s=85, color=SOCIAL_PREVIOUS_HIGH, zorder=6)
    ax.scatter(
        [current_x],
        [current.mean_temperature_c],
        s=230,
        color=SOCIAL_FOREGROUND,
        edgecolor=SOCIAL_BACKGROUND,
        linewidth=1.5,
        zorder=7,
    )
    ax.scatter([current_x], [current.mean_temperature_c], s=105, color=SOCIAL_PERIOD_COLOUR, zorder=8)
    ax.annotate(
        f"Previous high\n{previous['period_label']}: {previous.mean_temperature_c:.2f}°C",
        (previous_x, previous.mean_temperature_c),
        xytext=(-10, 24),
        textcoords="offset points",
        ha="right",
        va="bottom",
        color=SOCIAL_PREVIOUS_HIGH,
        fontsize=11,
        fontweight="bold",
    )
    ax.annotate(
        f"Latest\n{current.mean_temperature_c:.2f}°C",
        (current_x, current.mean_temperature_c),
        xytext=(-12, 24),
        textcoords="offset points",
        ha="right",
        va="bottom",
        color=SOCIAL_FOREGROUND,
        fontsize=12,
        fontweight="bold",
    )
    ax.set_xlabel("Window end (year)", fontsize=13, labelpad=12)
    ax.set_ylabel("Mean temperature (°C)", fontsize=13, labelpad=12)
    ax.set_xlim(float(data["end_x"].min()) - 0.5, float(data["end_x"].max()) + 0.5)
    ax.set_ylim(float(data["mean_temperature_c"].min()) - 0.25, float(data["mean_temperature_c"].max()) + 0.55)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(SOCIAL_GRID)
    legend = ax.legend(loc="lower right", frameon=True, fontsize=10)
    legend.get_frame().set_alpha(0.85)
    for text in legend.get_texts():
        text.set_color(SOCIAL_FOREGROUND)

    fig.text(0.07, 0.93, "WALES: ROLLING 12-MONTH", color=SOCIAL_FOREGROUND, fontsize=24, fontweight="bold", ha="left", va="top")
    fig.text(0.07, 0.885, "MEAN TEMPERATURE", color=SOCIAL_FOREGROUND, fontsize=24, fontweight="bold", ha="left", va="top")
    fig.text(0.07, 0.84, f"Latest complete window: {period}", color=SOCIAL_MUTED, fontsize=14, ha="left", va="top")
    fig.text(0.07, 0.77, f"{current.mean_temperature_c:.2f}°C", color=SOCIAL_PERIOD_COLOUR, fontsize=44, fontweight="bold", ha="left", va="top")
    fig.text(
        0.07,
        0.715,
        f"Ranks {rank} of {total} complete monthly-start windows",
        color=SOCIAL_FOREGROUND,
        fontsize=16,
        fontweight="bold",
        ha="left",
        va="top",
    )
    fig.text(
        0.07,
        0.678,
        f"Source updated {summary.get('source_last_updated', 'unknown')}.",
        color=SOCIAL_MUTED,
        fontsize=11.5,
        ha="left",
        va="top",
    )
    fig.text(
        0.07,
        0.03,
        "Monthly monitor refreshed on published Met Office Wales inputs.",
        color=SOCIAL_MUTED,
        fontsize=12.4,
        ha="left",
        va="bottom",
    )
    return _save(fig, basename, dpi=SOCIAL_DPI)


def run() -> dict[str, Path]:
    series, summary = _load()
    history_png, history_svg = render_history(series, summary)
    dark_png, dark_svg = render_dark_square(series, summary)
    return {
        "history_png": history_png,
        "history_svg": history_svg,
        "dark_png": dark_png,
        "dark_svg": dark_svg,
    }


if __name__ == "__main__":
    print(json.dumps({key: str(path) for key, path in run().items()}, indent=2))
