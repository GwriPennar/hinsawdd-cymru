"""Monthly rolling 12-month temperature monitor figures for Project 001."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

PROJECT_DIR = Path(__file__).resolve().parent
DERIVED_DIR = PROJECT_DIR / "data" / "derived"
FIGURES_DIR = PROJECT_DIR / "figures"
SERIES_PATH = DERIVED_DIR / "rolling_12_month_mean_temperature.csv"
SUMMARY_PATH = DERIVED_DIR / "summary.json"
HISTORY_BASENAME = FIGURES_DIR / "wales_rolling_12_month_temperature_history"
DARK_BASENAME = FIGURES_DIR / "wales_rolling_12_month_temperature_square_dark"

BACKGROUND = "#090b10"
FOREGROUND = "#f5f7fa"
MUTED = "#aab2bd"
GRID = "#303641"
TEMPERATURE_RED = "#ff4d5a"
MOVING_AVERAGE_CYAN = "#45e0e5"
PREVIOUS_HIGH_AMBER = "#ffd166"
REFERENCE_GREY = "#89919c"
LATEST_GOLD = "#f4c430"


def _load() -> tuple[pd.DataFrame, dict]:
    series = pd.read_csv(SERIES_PATH, parse_dates=["start_month", "end_month"])
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    return series, summary


def _save(fig: plt.Figure, basename: Path) -> tuple[Path, Path]:
    basename.parent.mkdir(parents=True, exist_ok=True)
    png = basename.with_suffix(".png")
    svg = basename.with_suffix(".svg")
    fig.savefig(png, dpi=150, facecolor=fig.get_facecolor(), bbox_inches="tight")
    fig.savefig(svg, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    return png, svg


def render_history(series: pd.DataFrame, summary: dict, basename: Path = HISTORY_BASENAME) -> tuple[Path, Path]:
    data = series.copy()
    data["end_year"] = data["end_month"].dt.year + (data["end_month"].dt.month / 12.0)
    data["trailing_10_window_mean_c"] = data["mean_temperature_c"].rolling(10, min_periods=10).mean()
    current = data.iloc[-1]
    previous = data.iloc[:-1].nlargest(1, "mean_temperature_c").iloc[0]
    reference = float(summary["derived_reference_1991_2020_c"])

    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams.update({"svg.fonttype": "none"})
    fig, ax = plt.subplots(figsize=(12, 6.5))
    sns.lineplot(data=data, x="end_year", y="mean_temperature_c", ax=ax, linewidth=1.1, alpha=0.72)
    sns.lineplot(
        data=data,
        x="end_year",
        y="trailing_10_window_mean_c",
        ax=ax,
        linewidth=2.8,
        color=MOVING_AVERAGE_CYAN,
        label="Trailing 10-window average",
    )
    ax.axhline(reference, linestyle=":", linewidth=1.1, color=REFERENCE_GREY, label="Derived 1991–2020 reference")
    def end_fraction(row: pd.Series) -> float:
        return float(row["end_month"].year) + float(row["end_month"].month) / 12.0

    prev_x = end_fraction(previous)
    curr_x = end_fraction(current)
    ax.scatter([prev_x], [previous.mean_temperature_c], s=45, zorder=5)
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
    ax.set_xlim(float(data["end_year"].min()) - 0.5, float(data["end_year"].max()) + 0.5)
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
    return _save(fig, basename)


def render_dark_square(series: pd.DataFrame, summary: dict, basename: Path = DARK_BASENAME) -> tuple[Path, Path]:
    data = series.copy()
    data["end_year"] = data["end_month"].dt.year
    data["trailing_10_window_mean_c"] = data["mean_temperature_c"].rolling(10, min_periods=10).mean()
    current = data.iloc[-1]
    previous = data.iloc[:-1].nlargest(1, "mean_temperature_c").iloc[0]
    reference = float(summary["derived_reference_1991_2020_c"])
    period = summary["current_window"]["period_label"]
    rank = int(summary["current_window"]["rank_warmest"])
    total = int(summary["current_window"]["window_count"])

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
    sns.lineplot(data=data, x="end_year", y="mean_temperature_c", ax=ax, linewidth=1.7, alpha=0.58, color=TEMPERATURE_RED)
    sns.lineplot(
        data=data,
        x="end_year",
        y="trailing_10_window_mean_c",
        ax=ax,
        linewidth=4.4,
        color=MOVING_AVERAGE_CYAN,
        label="Trailing 10-window average",
    )
    ax.axhline(reference, linestyle="--", linewidth=1.4, color=REFERENCE_GREY, alpha=0.85, label="Derived 1991–2020 reference")
    ax.scatter([previous.end_year], [previous.mean_temperature_c], s=85, color=PREVIOUS_HIGH_AMBER, zorder=6)
    ax.scatter([current.end_year], [current.mean_temperature_c], s=230, color=FOREGROUND, edgecolor=BACKGROUND, linewidth=1.5, zorder=7)
    ax.scatter([current.end_year], [current.mean_temperature_c], s=105, color=TEMPERATURE_RED, zorder=8)
    ax.set_xlabel("Window end year", fontsize=13, labelpad=12)
    ax.set_ylabel("Mean temperature (°C)", fontsize=13, labelpad=12)
    ax.set_xlim(int(data["end_year"].min()), int(data["end_year"].max()) + 3)
    ax.set_ylim(float(data["mean_temperature_c"].min()) - 0.25, float(data["mean_temperature_c"].max()) + 0.55)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="lower right", frameon=True, fontsize=10)

    fig.text(0.07, 0.93, "WALES: ROLLING 12-MONTH", color=FOREGROUND, fontsize=24, fontweight="bold", ha="left", va="top")
    fig.text(0.07, 0.885, "MEAN TEMPERATURE", color=FOREGROUND, fontsize=24, fontweight="bold", ha="left", va="top")
    fig.text(0.07, 0.84, f"Latest complete window: {period}", color=MUTED, fontsize=14, ha="left", va="top")
    fig.text(0.07, 0.77, f"{current.mean_temperature_c:.2f}°C", color=TEMPERATURE_RED, fontsize=44, fontweight="bold", ha="left", va="top")
    fig.text(
        0.07,
        0.715,
        f"Ranks {rank} of {total} complete monthly-start windows",
        color=FOREGROUND,
        fontsize=16,
        fontweight="bold",
        ha="left",
        va="top",
    )
    fig.text(
        0.07,
        0.03,
        "Monthly monitor refreshed on published Met Office Wales inputs.",
        color=MUTED,
        fontsize=12.4,
        ha="left",
        va="bottom",
    )
    return _save(fig, basename)


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
