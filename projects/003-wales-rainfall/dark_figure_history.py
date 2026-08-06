"""Historical rainfall and July renderers."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from dark_climate_constants import BLUE, CYAN, DRY, DRY_STRONG, MUTED, PANEL_BG, TEXT, WET, WHITE
from dark_figure_style import _finish, _new_figure, _theme

def render_history(data: pd.DataFrame, output: Path, *, square: bool, source_note: str) -> None:
    fig, ax = _new_figure(square)
    reference = float(data["reference_1991_2020_mm"].iloc[0])
    wettest = data.nlargest(1, "rainfall_total_mm").iloc[0]
    driest = data.nsmallest(1, "rainfall_total_mm").iloc[0]
    latest = data.iloc[-1]
    ax.plot(data["end_year"], data["rainfall_total_mm"], color=BLUE, linewidth=1.15, alpha=0.55, label="August–July total")
    ax.plot(data["end_year"], data["trailing_10_period_mean_mm"], color=CYAN, linewidth=3.1, label="Trailing 10-period mean")
    ax.axhline(reference, color=WHITE, linestyle="--", linewidth=1.6, alpha=0.75, label="1991–2020 reference")
    annotations = [
        (driest, "Driest", (10, 12), "left"),
        (wettest, "Wettest", (-12, -48), "right"),
        (latest, "Latest", (-10, 14), "right"),
    ]
    if square:
        annotations = [(driest, "Driest", (8, 10), "left"), (latest, "Latest", (-8, 12), "right")]
    for row, label, offset, alignment in annotations:
        ax.scatter([row.end_year], [row.rainfall_total_mm], color=WHITE, edgecolor=PANEL_BG, s=62, zorder=7)
        ax.annotate(
            f"{label}: {row.rainfall_total_mm:.1f} mm\n{row.period}",
            (row.end_year, row.rainfall_total_mm),
            xytext=offset,
            textcoords="offset points",
            ha=alignment,
            fontsize=8.5 if square else 9.5,
            color=TEXT,
        )
    ax.set_title("Wales rainfall history", fontsize=23 if square else 25, fontweight="bold", pad=18, loc="left")
    ax.text(0, 1.01, "Complete August-to-July totals since records began", transform=ax.transAxes, color=MUTED, fontsize=11 if square else 12)
    ax.set_xlabel("Period end year")
    ax.set_ylabel("Total precipitation (mm)")
    ax.legend(loc="upper left", fontsize=8.5 if square else 9.5, ncol=1 if square else 3, frameon=True)
    _finish(fig, ax, output, square=square, source_note=source_note)


def render_july_history(data: pd.DataFrame, output: Path, *, square: bool, source_note: str) -> None:
    fig, ax = _new_figure(square)
    reference = float(data["reference_1991_2020_mm"].iloc[0])
    latest = data.iloc[-1]
    colors = np.where(data["july_rainfall_mm"] < reference, DRY, WET).astype(object)
    colors[-1] = DRY_STRONG
    ax.bar(data["year"], data["july_rainfall_mm"], color=colors, width=1.0, alpha=0.85)
    ax.plot(data["year"], data["trailing_10_year_mean_mm"], color=WHITE, linewidth=2.5, label="Trailing 10-year mean")
    ax.axhline(reference, color=CYAN, linestyle="--", linewidth=1.8, label="1991–2020 July reference")
    ax.scatter([latest.year], [latest.july_rainfall_mm], color=WHITE, s=78, zorder=8)
    ax.text(
        0.985,
        0.955,
        f"JULY {int(latest.year)}\n{latest.july_rainfall_mm:.1f} mm\n{latest.percentage_of_1991_2020:.1f}% of normal",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=9.5 if square else 10.5,
        fontweight="bold",
        color=TEXT,
        bbox={
            "boxstyle": "round,pad=0.55",
            "facecolor": PANEL_BG,
            "edgecolor": DRY_STRONG,
            "linewidth": 1.25,
            "alpha": 0.96,
        },
    )
    ax.set_title("How dry was July 2026 in Wales?", fontsize=22 if square else 25, fontweight="bold", pad=18, loc="left")
    ax.text(
        0,
        1.01,
        f"{latest.july_rainfall_mm:.1f} mm: driest July in the Wales series beginning 1836",
        transform=ax.transAxes,
        color=MUTED,
        fontsize=10.5 if square else 12,
    )
    ax.set_xlabel("Year")
    ax.set_ylabel("July precipitation (mm)")
    ax.legend(loc="upper left", fontsize=8.5 if square else 9.5, frameon=True)
    _finish(fig, ax, output, square=square, source_note=source_note)

