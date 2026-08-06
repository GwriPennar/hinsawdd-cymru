"""Rainfall anomaly and rain-day renderers."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from dark_climate_constants import BLUE, CYAN, DRY, MUTED, TEXT, WET, WHITE
from dark_figure_style import _finish, _new_figure, _theme

def render_dryness(data: pd.DataFrame, output: Path, *, square: bool, source_note: str) -> None:
    fig, ax = _new_figure(square)
    colors = np.where(data["anomaly_percent"] < 0, DRY, WET)
    ax.bar(data["end_year"], data["anomaly_percent"], color=colors, width=1.0, alpha=0.88)
    ax.plot(data["end_year"], data["trailing_10_period_anomaly_percent"], color=WHITE, linewidth=2.6, label="Trailing 10-period mean")
    ax.axhline(0, color=CYAN, linewidth=1.6)
    latest = data.iloc[-1]
    ax.scatter([latest.end_year], [latest.anomaly_percent], color=WHITE, s=68, zorder=7)
    ax.annotate(
        f"{latest.period}\n{latest.anomaly_percent:+.1f}%",
        (latest.end_year, latest.anomaly_percent),
        xytext=(-10, 14 if latest.anomaly_percent >= 0 else -36),
        textcoords="offset points",
        ha="right",
        fontsize=8.5 if square else 9.5,
        color=TEXT,
    )
    ax.set_title("Wales rainfall dryness and wetness", fontsize=22 if square else 25, fontweight="bold", pad=18, loc="left")
    ax.text(
        0,
        1.01,
        "August-to-July rainfall difference from the 1991–2020 reference",
        transform=ax.transAxes,
        color=MUTED,
        fontsize=10.5 if square else 12,
    )
    ax.set_xlabel("Period end year")
    ax.set_ylabel("Difference from 1991–2020 (%)")
    ax.legend(loc="upper left", fontsize=8.5 if square else 9.5, frameon=True)
    _finish(fig, ax, output, square=square, source_note=source_note)


def render_raindays(data: pd.DataFrame, output: Path, *, square: bool, source_note: str) -> None:
    fig, ax = _new_figure(square)
    reference = float(data["reference_1991_2020_days"].iloc[0])
    latest = data.iloc[-1]
    fewest = data.nsmallest(1, "rain_days_ge_1mm").iloc[0]
    ax.plot(data["end_year"], data["rain_days_ge_1mm"], color=BLUE, linewidth=1.2, alpha=0.58, label="Days with at least 1 mm")
    ax.plot(data["end_year"], data["trailing_10_period_mean_days"], color=CYAN, linewidth=3.0, label="Trailing 10-period mean")
    ax.axhline(reference, color=WHITE, linestyle="--", linewidth=1.6, alpha=0.75, label="1991–2020 reference")
    for row, label, offset, alignment in [
        (fewest, "Fewest", (10, 12), "left"),
        (latest, "Latest", (-10, 14), "right"),
    ]:
        ax.scatter([row.end_year], [row.rain_days_ge_1mm], color=WHITE, s=64, zorder=7)
        ax.annotate(
            f"{label}: {row.rain_days_ge_1mm:.1f} days\n{row.period}",
            (row.end_year, row.rain_days_ge_1mm),
            xytext=offset,
            textcoords="offset points",
            ha=alignment,
            fontsize=8.5 if square else 9.5,
            color=TEXT,
        )
    ax.set_title("How often does it rain in Wales?", fontsize=22 if square else 25, fontweight="bold", pad=18, loc="left")
    ax.text(
        0,
        1.01,
        "Complete August-to-July count of days with at least 1 mm precipitation",
        transform=ax.transAxes,
        color=MUTED,
        fontsize=10.5 if square else 12,
    )
    ax.set_xlabel("Period end year")
    ax.set_ylabel("Rain days ≥1 mm")
    ax.legend(loc="upper left", fontsize=8.5 if square else 9.5, frameon=True)
    _finish(fig, ax, output, square=square, source_note=source_note)

