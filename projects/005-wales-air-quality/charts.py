"""Dark-mode chart renderer for Project 005."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import seaborn as sns

FIG_BG = "#080c16"
AX_BG = "#0f172a"
TEXT = "#f8fafc"
MUTED = "#94a3b8"
GRID = "#334155"
CYAN = "#22d3ee"

SITE_TYPE_MARKERS = {
    "Urban Background": "o",
    "Urban Traffic": "s",
    "Urban Industrial": "^",
    "Rural Background": "D",
}

SOURCE = "Source: DEFRA UK-AIR, Automatic Urban and Rural Network (AURN). Recent data may be provisional."


def _apply_dark(ax):
    ax.set_facecolor(AX_BG)
    ax.tick_params(colors=MUTED, labelsize=9)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.grid(True, color=GRID, alpha=0.38, linewidth=0.7)
    ax.set_axisbelow(True)
    ax.xaxis.label.set_color(MUTED)
    ax.yaxis.label.set_color(MUTED)


def _footer(fig, text=SOURCE):
    fig.text(0.01, 0.012, text, color=MUTED, fontsize=8, ha="left", va="bottom")


def _save(fig, output_base: Path):
    output_base.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_base.with_suffix(".png"), dpi=100, facecolor=FIG_BG, bbox_inches=None)
    fig.savefig(output_base.with_suffix(".svg"), facecolor=FIG_BG, bbox_inches=None)
    plt.close(fig)


def _new_figure(square: bool):
    if square:
        fig, ax = plt.subplots(figsize=(10.8, 10.8), dpi=100)
    else:
        fig, ax = plt.subplots(figsize=(16, 9), dpi=100)
    fig.patch.set_facecolor(FIG_BG)
    _apply_dark(ax)
    return fig, ax


def _header(ax, title: str, subtitle: str):
    ax.set_title(title, loc="left", color=TEXT, fontsize=20, fontweight="bold", pad=24)
    ax.text(0, 1.015, subtitle, transform=ax.transAxes, color=MUTED, fontsize=10, va="bottom")


def _station_palette(names):
    colors = sns.color_palette("icefire", n_colors=max(3, len(names)))
    return dict(zip(sorted(names), colors))


def line_chart(data, output_dir, filename, title, subtitle, square):
    fig, ax = _new_figure(square)
    _header(ax, title, subtitle)
    work = data.copy()
    work["pm25"] = pd.to_numeric(work["pm25"], errors="coerce")
    palette = _station_palette(work["station_name"].dropna().unique())
    for name, group in work.groupby("station_name"):
        valid = group.dropna(subset=["pm25"])
        if valid.empty:
            continue
        ax.plot(valid["date"], valid["pm25"], label=name, linewidth=1.45 if square else 1.35,
                alpha=0.9, color=palette[name])
    ax.set_ylabel("Daily mean PM₂.₅ (µg/m³)")
    ax.set_xlabel("Date")
    ax.set_ylim(bottom=0)
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=5, maxticks=10))
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))
    legend = ax.legend(loc="upper left", ncol=1 if square else 2, fontsize=8.5,
                       frameon=True, facecolor=AX_BG, edgecolor=GRID)
    for text in legend.get_texts():
        text.set_color(TEXT)
    fig.subplots_adjust(left=0.09, right=0.98, top=0.86, bottom=0.13)
    _footer(fig)
    _save(fig, output_dir / filename)


def distribution_chart(data, output_dir, square):
    fig, ax = _new_figure(square)
    _header(ax, "Wales AURN PM₂.₅ distribution by monitoring station",
            "Daily means in the latest rolling 12-month window; site types are kept separate.")
    work = data.copy()
    work["pm25"] = pd.to_numeric(work["pm25"], errors="coerce")
    work = work.dropna(subset=["pm25"])
    order = work.groupby("station_name")["pm25"].median().sort_values().index.tolist()
    sns.boxplot(data=work, x="pm25", y="station_name", order=order, ax=ax,
                color=CYAN, width=0.55, fliersize=2, linewidth=1)
    ax.set_xlabel("Daily mean PM₂.₅ (µg/m³)")
    ax.set_ylabel("")
    ax.grid(True, axis="x", color=GRID, alpha=0.38)
    ax.grid(False, axis="y")
    fig.subplots_adjust(left=0.24 if not square else 0.28, right=0.98, top=0.86, bottom=0.12)
    _footer(fig)
    suffix = "_square" if square else ""
    _save(fig, output_dir / f"wales_aurn_pm25_station_distribution_dark{suffix}")


def station_map(stations, output_dir, square):
    fig, ax = _new_figure(square)
    _header(ax, "Reference-grade PM₂.₅ monitoring sites used in Project 005",
            "Welsh AURN baseline stations; position shown by longitude and latitude, not a modelled pollution surface.")
    types = sorted({s.site_type for s in stations})
    colors = sns.color_palette("icefire", n_colors=max(3, len(types)))
    color_by_type = dict(zip(types, colors))
    for station in stations:
        ax.scatter(station.longitude, station.latitude, s=100 if square else 85,
                   marker=SITE_TYPE_MARKERS.get(station.site_type, "o"),
                   color=color_by_type[station.site_type], edgecolor=TEXT, linewidth=0.7,
                   zorder=3, label=station.site_type)
        ax.annotate(station.name, (station.longitude, station.latitude), xytext=(6, 6),
                    textcoords="offset points", color=TEXT, fontsize=8.5)
    handles, labels = ax.get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    legend = ax.legend(unique.values(), unique.keys(), loc="lower right", fontsize=8.5,
                       facecolor=AX_BG, edgecolor=GRID)
    for text in legend.get_texts():
        text.set_color(TEXT)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_xlim(-5.0, -2.4)
    ax.set_ylim(51.35, 53.25)
    fig.subplots_adjust(left=0.09, right=0.98, top=0.86, bottom=0.12)
    _footer(fig, "Source: DEFRA UK-AIR site metadata. Coordinates are monitoring-site locations.")
    suffix = "_square" if square else ""
    _save(fig, output_dir / f"wales_aurn_pm25_station_map_dark{suffix}")


def render_all_charts(daily, stations, metadata, output_dir):
    sns.set_theme(context="notebook", style="darkgrid")
    output_dir = Path(output_dir)
    latest = pd.Timestamp(metadata["latest_observation_day_utc"])
    rolling_start = pd.Timestamp(metadata["rolling_start_utc"])
    recent_start = pd.Timestamp(metadata["recent_start_utc"])
    rolling = daily[daily["date"].between(rolling_start, latest)].copy()
    recent = daily[daily["date"].between(recent_start, latest)].copy()

    rolling_subtitle = (f"Daily means, {rolling_start:%d %b %Y} to {latest:%d %b %Y}; "
                        "minimum 18 valid hourly values per station-day.")
    recent_subtitle = (f"Recent {metadata['recent_days']}-day window, {recent_start:%d %b %Y} to "
                       f"{latest:%d %b %Y}; observations only, no wildfire attribution.")
    for square in (False, True):
        suffix = "_square" if square else ""
        line_chart(rolling, output_dir, f"wales_aurn_pm25_rolling_year_dark{suffix}",
                   "Measured PM₂.₅ across Wales: latest rolling year", rolling_subtitle, square)
        line_chart(recent, output_dir, f"wales_aurn_pm25_recent_dark{suffix}",
                   "Measured PM₂.₅ across Wales: recent dry-period window", recent_subtitle, square)
        distribution_chart(rolling, output_dir, square)
        station_map(stations, output_dir, square)
