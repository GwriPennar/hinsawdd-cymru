"""Shared dark chart styling and export helpers."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns

from dark_climate_constants import DARK_BG, GRID, MUTED, PANEL_BG, TEXT

def _theme() -> None:
    sns.set_theme(style="darkgrid", context="talk")
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "svg.fonttype": "none",
            "figure.facecolor": DARK_BG,
            "axes.facecolor": PANEL_BG,
            "axes.edgecolor": GRID,
            "axes.labelcolor": TEXT,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "text.color": TEXT,
            "grid.color": GRID,
            "grid.alpha": 0.45,
            "legend.facecolor": PANEL_BG,
            "legend.edgecolor": GRID,
            "legend.labelcolor": TEXT,
        }
    )


def _new_figure(square: bool) -> tuple[plt.Figure, plt.Axes]:
    _theme()
    size = (10.8, 10.8) if square else (16, 9)
    return plt.subplots(figsize=size, dpi=100)


def _finish(
    fig: plt.Figure,
    ax: plt.Axes,
    output: Path,
    *,
    square: bool,
    source_note: str,
) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRID)
    fig.text(0.02, 0.018, source_note, color=MUTED, fontsize=7.8 if square else 8.5, ha="left")
    fig.subplots_adjust(left=0.10 if square else 0.08, right=0.97, top=0.88, bottom=0.12)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output.with_suffix(".png"), dpi=100, facecolor=DARK_BG)
    fig.savefig(output.with_suffix(".svg"), facecolor=DARK_BG)
    plt.close(fig)
