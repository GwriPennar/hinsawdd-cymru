"""Shared trend-chart renderers for Project 001 August–July and rolling monitors."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from figure_style import (
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


@dataclass(frozen=True)
class PointAnnotation:
    x: float
    y: float
    text: str
    color: str | None = None
    fontsize: float = 8
    fontweight: str | None = None
    xytext: tuple[float, float] = (-12, 18)
    ha: str = "right"


@dataclass(frozen=True)
class LightTrendConfig:
    title: str
    xlabel: str
    ylabel: str
    footer: str
    label_individual: str
    label_average: str
    label_reference: str
    x_col: str
    y_col: str
    trailing_col: str
    previous: PointAnnotation
    current: PointAnnotation
    xlim_pad: float = 2.0
    previous_marker_color: str | None = None
    current_marker_color: str = "#f4c430"


@dataclass(frozen=True)
class SocialHeadline:
    title_line1: str
    title_line2: str
    subtitle: str
    headline_value: str
    headline_value_color: str
    claim: str
    note: str
    footer1: str
    footer2: str = ""


@dataclass(frozen=True)
class SocialDarkConfig:
    label_individual: str
    label_average: str
    label_reference: str
    x_col: str
    y_col: str
    trailing_col: str
    previous: PointAnnotation
    current: PointAnnotation
    headline: SocialHeadline
    xlim_pad: float = 3.0


def _save_figure(
    fig: plt.Figure,
    output_base: Path,
    *,
    dpi: int,
    facecolor: str | None = None,
    bbox_inches: str | None = None,
) -> tuple[Path, Path]:
    output_base.parent.mkdir(parents=True, exist_ok=True)
    png = output_base.with_suffix(".png")
    svg = output_base.with_suffix(".svg")
    kwargs: dict[str, object] = {}
    if facecolor is not None:
        kwargs["facecolor"] = facecolor
    if bbox_inches is not None:
        kwargs["bbox_inches"] = bbox_inches
    fig.savefig(png, dpi=dpi, **kwargs)
    fig.savefig(svg, **kwargs)
    plt.close(fig)
    return png, svg


def render_light_trend(
    data: pd.DataFrame,
    output_base: Path,
    *,
    reference_c: float,
    config: LightTrendConfig,
    bbox_inches: str | None = "tight",
) -> tuple[Path, Path]:
    frame = data.copy()
    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams.update({"svg.fonttype": "none"})
    fig, ax = plt.subplots(figsize=LIGHT_TREND_FIGSIZE)
    sns.lineplot(
        data=frame,
        x=config.x_col,
        y=config.y_col,
        ax=ax,
        color=LIGHT_PERIOD_COLOUR,
        linewidth=1.1,
        alpha=0.72,
        label=config.label_individual,
        zorder=2,
    )
    sns.lineplot(
        data=frame,
        x=config.x_col,
        y=config.trailing_col,
        ax=ax,
        color=LIGHT_AVERAGE_COLOUR,
        linewidth=2.8,
        label=config.label_average,
        zorder=4,
    )
    ax.axhline(
        reference_c,
        color=LIGHT_REFERENCE_COLOUR,
        linestyle=":",
        linewidth=1.1,
        label=config.label_reference,
        zorder=1,
    )
    prev_color = config.previous_marker_color or SOCIAL_PREVIOUS_HIGH
    ax.scatter([config.previous.x], [config.previous.y], s=45, color=prev_color, zorder=5)
    ax.scatter([config.current.x], [config.current.y], s=70, color=config.current_marker_color, zorder=6)
    for point in (config.previous, config.current):
        ax.annotate(
            point.text,
            (point.x, point.y),
            xytext=point.xytext,
            textcoords="offset points",
            ha=point.ha,
            fontsize=point.fontsize,
            color=point.color,
            fontweight=point.fontweight,
        )
    ax.set(title=config.title, xlabel=config.xlabel, ylabel=config.ylabel)
    xmin = float(frame[config.x_col].min())
    xmax = float(frame[config.x_col].max())
    ax.set_xlim(xmin - 0.5 if config.x_col != "end_year" else int(xmin), xmax + config.xlim_pad)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper left")
    fig.text(0.01, 0.01, config.footer, fontsize=7)
    fig.tight_layout(rect=(0, 0.045, 1, 1))
    return _save_figure(
        fig,
        output_base,
        dpi=LIGHT_TREND_DPI,
        bbox_inches=bbox_inches,
    )


def render_social_dark(
    data: pd.DataFrame,
    output_base: Path,
    *,
    reference_c: float,
    config: SocialDarkConfig,
) -> tuple[Path, Path]:
    frame = data.copy()
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
        data=frame,
        x=config.x_col,
        y=config.y_col,
        ax=ax,
        color=SOCIAL_PERIOD_COLOUR,
        linewidth=1.7,
        alpha=0.58,
        label=config.label_individual,
        zorder=2,
    )
    sns.lineplot(
        data=frame,
        x=config.x_col,
        y=config.trailing_col,
        ax=ax,
        color=SOCIAL_AVERAGE_COLOUR,
        linewidth=4.4,
        label=config.label_average,
        zorder=4,
    )
    ax.axhline(
        reference_c,
        color=SOCIAL_REFERENCE_COLOUR,
        linestyle="--",
        linewidth=1.4,
        alpha=0.85,
        label=config.label_reference,
        zorder=1,
    )
    ax.scatter(
        [config.previous.x],
        [config.previous.y],
        s=85,
        color=SOCIAL_PREVIOUS_HIGH,
        edgecolor=SOCIAL_BACKGROUND,
        linewidth=1.5,
        zorder=6,
    )
    ax.scatter(
        [config.current.x],
        [config.current.y],
        s=230,
        color=SOCIAL_FOREGROUND,
        edgecolor=SOCIAL_BACKGROUND,
        linewidth=1.5,
        zorder=7,
    )
    ax.scatter(
        [config.current.x],
        [config.current.y],
        s=105,
        color=SOCIAL_PERIOD_COLOUR,
        zorder=8,
    )
    for point in (config.previous, config.current):
        ax.annotate(
            point.text,
            (point.x, point.y),
            xytext=point.xytext,
            textcoords="offset points",
            ha=point.ha,
            va="bottom",
            color=point.color or SOCIAL_FOREGROUND,
            fontsize=point.fontsize,
            fontweight=point.fontweight,
        )
    xmin = float(frame[config.x_col].min())
    xmax = float(frame[config.x_col].max())
    ax.set_xlim(xmin - 0.5, xmax + config.xlim_pad)
    ax.set_ylim(float(frame[config.y_col].min()) - 0.25, float(frame[config.y_col].max()) + 0.55)
    ax.set_xlabel("Window end (year)" if config.x_col == "end_x" else "Period end year", fontsize=13, labelpad=12)
    ax.set_ylabel("Mean temperature (°C)", fontsize=13, labelpad=12)
    ax.tick_params(axis="both", labelsize=11)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(SOCIAL_GRID)
    legend = ax.legend(loc="lower right", frameon=True, fontsize=10, borderpad=0.8, labelspacing=0.6)
    legend.get_frame().set_alpha(0.85)
    for text in legend.get_texts():
        text.set_color(SOCIAL_FOREGROUND)

    headline = config.headline
    fig.text(0.07, 0.93, headline.title_line1, color=SOCIAL_FOREGROUND, fontsize=24, fontweight="bold", ha="left", va="top")
    if headline.title_line2:
        fig.text(0.07, 0.885, headline.title_line2, color=SOCIAL_FOREGROUND, fontsize=24, fontweight="bold", ha="left", va="top")
        subtitle_y = 0.84
        value_y = 0.77
        claim_y = 0.715
        note_y = 0.678
    else:
        subtitle_y = 0.885
        value_y = 0.81
        claim_y = 0.75
        note_y = 0.715
    fig.text(0.07, subtitle_y, headline.subtitle, color=SOCIAL_MUTED, fontsize=14, ha="left", va="top")
    fig.text(0.07, value_y, headline.headline_value, color=headline.headline_value_color, fontsize=44, fontweight="bold", ha="left", va="top")
    fig.text(0.07, claim_y, headline.claim, color=SOCIAL_FOREGROUND, fontsize=16, fontweight="bold", ha="left", va="top")
    fig.text(0.07, note_y, headline.note, color=SOCIAL_MUTED, fontsize=11.5, ha="left", va="top")
    fig.text(0.07, 0.08, headline.footer1, color=SOCIAL_MUTED, fontsize=9.5, ha="left", va="bottom")
    if headline.footer2:
        fig.text(0.07, 0.05, headline.footer2, color=SOCIAL_MUTED, fontsize=9.5, ha="left", va="bottom")
    return _save_figure(fig, output_base, dpi=SOCIAL_DPI, facecolor=SOCIAL_BACKGROUND)
