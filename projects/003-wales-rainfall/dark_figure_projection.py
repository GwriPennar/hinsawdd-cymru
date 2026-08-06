"""Illustrative statistical-continuation renderer."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from dark_climate_constants import BLUE, CYAN, DRY, MUTED, WET, WHITE, LinearFit
from dark_figure_style import _finish, _new_figure, _theme

def render_projection(
    history: pd.DataFrame,
    projection: pd.DataFrame,
    fits: dict[str, LinearFit],
    output: Path,
    *,
    square: bool,
    source_note: str,
) -> None:
    fig, ax = _new_figure(square)
    primary = fits["primary"]
    full = fits["full"]
    robust = fits["robust"]
    future = projection[projection["end_year"] >= primary.last_year]
    years = future["end_year"].to_numpy(dtype=float)
    ax.plot(history["end_year"], history["rainfall_total_mm"], color=BLUE, linewidth=1.0, alpha=0.28, label="Observed periods")
    ax.plot(history["end_year"], history["trailing_10_period_mean_mm"], color=CYAN, linewidth=2.8, label="Trailing 10-period mean")
    fit_years = np.arange(primary.first_year, primary.last_year + 1)
    ax.plot(fit_years, primary.predict(fit_years), color=WHITE, linewidth=2.4, label=f"Modern fit, {primary.first_year}–{primary.last_year}")
    ax.fill_between(years, future["bootstrap_95_lower_mm"], future["bootstrap_95_upper_mm"], color=BLUE, alpha=0.16, label="95% trend-fit bootstrap range")
    ax.plot(years, future["primary_projection_mm"], color=DRY, linewidth=2.8, linestyle="--", label="Illustrative continuation")
    if not square:
        ax.plot(years, full.predict(years), color=MUTED, linewidth=1.5, linestyle=":", label="Full-record sensitivity")
        ax.plot(years, robust.predict(years), color=WET, linewidth=1.5, linestyle="-.", label="Theil–Sen sensitivity")
    ax.axvline(primary.last_year, color=MUTED, linewidth=1.2, linestyle=":")
    for milestone in (2050, 2100):
        row = projection.loc[projection["end_year"] == milestone].iloc[0]
        ax.scatter([milestone], [row.primary_projection_mm], color=WHITE, s=68, zorder=8)
        ax.annotate(
            f"{milestone}: {row.primary_projection_mm:.0f} mm",
            (milestone, row.primary_projection_mm),
            xytext=(-8, 14),
            textcoords="offset points",
            ha="right",
            fontsize=8.5 if square else 9.5,
        )
    ax.set_title("Wales rainfall: statistical continuation", fontsize=22 if square else 25, fontweight="bold", pad=18, loc="left")
    ax.text(
        0,
        1.01,
        "Observed August-to-July totals; transparent trend sensitivities, not a physical climate forecast",
        transform=ax.transAxes,
        color=MUTED,
        fontsize=10 if square else 11.5,
    )
    ax.set_xlabel("Period end year")
    ax.set_ylabel("Total precipitation (mm)")
    ax.legend(loc="upper left", fontsize=7.8 if square else 8.8, ncol=1 if square else 2, frameon=True)
    _finish(fig, ax, output, square=square, source_note=source_note)
