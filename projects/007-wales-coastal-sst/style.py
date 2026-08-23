"""Dark-mode figure helpers for Project 007."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns

from constants import DARK_BG, GRID, MUTED, PANEL_BG, TEXT


def theme() -> None:
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


def new_figure(*, square: bool):
    theme()
    size = (10.8, 10.8) if square else (16, 9)
    return plt.subplots(figsize=size, dpi=100)


def new_figure_panels(*, square: bool, nrows: int = 2, height_ratios=(3, 1)):
    theme()
    size = (10.8, 10.8) if square else (16, 9)
    return plt.subplots(
        nrows,
        1,
        figsize=size,
        dpi=100,
        sharex=True,
        gridspec_kw={"height_ratios": list(height_ratios), "hspace": 0.08},
    )


def finish(fig, output: Path, *, square: bool, source_note: str) -> None:
    for ax in fig.axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["left", "bottom"]].set_color(GRID)
    fig.text(0.02, 0.015, source_note, color=MUTED, fontsize=7.5 if square else 8.2, ha="left")
    fig.subplots_adjust(
        left=0.11 if square else 0.07,
        right=0.97,
        top=0.88 if square else 0.90,
        bottom=0.12,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output.with_suffix(".png"), dpi=100, facecolor=DARK_BG)
    fig.savefig(output.with_suffix(".svg"), facecolor=DARK_BG)
    plt.close(fig)
