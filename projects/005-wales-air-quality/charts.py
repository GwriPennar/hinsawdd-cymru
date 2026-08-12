"""Dark-mode chart renderer for Project 005."""
from __future__ import annotations

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
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
SOURCE = (
    "Source: DEFRA UK-AIR, AURN. Recent data may be provisional. "
    "QC-screened values are a sensitivity view; raw data retained."
)


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


def _save(fig, base):
    base = Path(base)
    base.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(base.with_suffix(".png"), dpi=100, facecolor=FIG_BG, bbox_inches=None)
    fig.savefig(base.with_suffix(".svg"), facecolor=FIG_BG, bbox_inches=None)
    plt.close(fig)


def _new(square):
    fig, ax = plt.subplots(figsize=(10.8, 10.8) if square else (16, 9), dpi=100)
    fig.patch.set_facecolor(FIG_BG)
    _apply_dark(ax)
    return fig, ax


def _header(ax, title, subtitle):
    ax.set_title(title, loc="left", color=TEXT, fontsize=20, fontweight="bold", pad=24)
    ax.text(
        0,
        1.015,
        subtitle,
        transform=ax.transAxes,
        color=MUTED,
        fontsize=10,
        va="bottom",
    )


def _palette(names):
    colors = ["#22d3ee", "#60a5fa", "#a78bfa", "#f59e0b", "#fb7185", "#f43f5e", "#34d399"]
    return {name: colors[index % len(colors)] for index, name in enumerate(sorted(names))}


def line_chart(data, out, filename, title, subtitle, square):
    fig, ax = _new(square)
    _header(ax, title, subtitle)
    work = data.copy()
    value_col = "pm25_screened" if "pm25_screened" in work else "pm25"
    work[value_col] = pd.to_numeric(work[value_col], errors="coerce")
    palette = _palette(work["station_name"].dropna().unique())
    for name, group in work.groupby("station_name"):
        valid = group.dropna(subset=[value_col])
        if not valid.empty:
            ax.plot(
                valid["date"],
                valid[value_col],
                label=name,
                linewidth=1.45 if square else 1.35,
                alpha=0.9,
                color=palette[name],
            )
    ax.set_ylabel("Daily mean PM₂.₅ (µg/m³)")
    ax.set_xlabel("Date")
    ax.set_ylim(bottom=0)
    locator = mdates.AutoDateLocator(minticks=5, maxticks=10)
    formatter = mdates.ConciseDateFormatter(locator)
    formatter.show_offset = False
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    legend = ax.legend(
        loc="upper left",
        ncol=1 if square else 2,
        fontsize=8.5,
        frameon=True,
        facecolor=AX_BG,
        edgecolor=GRID,
    )
    for text in legend.get_texts():
        text.set_color(TEXT)
    fig.subplots_adjust(left=0.09, right=0.98, top=0.86, bottom=0.13)
    _footer(fig)
    _save(fig, Path(out) / filename)


def distribution_chart(data, out, square):
    fig, ax = _new(square)
    _header(
        ax,
        "Wales AURN PM₂.₅ distribution by monitoring station",
        "QC-screened daily means in the latest rolling 12-month window; site types remain explicit.",
    )
    work = data.copy()
    value_col = "pm25_screened" if "pm25_screened" in work else "pm25"
    work[value_col] = pd.to_numeric(work[value_col], errors="coerce")
    work = work.dropna(subset=[value_col])
    order = work.groupby("station_name")[value_col].median().sort_values().index.tolist()
    sns.boxplot(
        data=work,
        x=value_col,
        y="station_name",
        order=order,
        ax=ax,
        color=CYAN,
        width=0.55,
        fliersize=2,
        linewidth=1,
    )
    ax.set_xlabel("Daily mean PM₂.₅ (µg/m³)")
    ax.set_ylabel("")
    ax.grid(True, axis="x", color=GRID, alpha=0.38)
    ax.grid(False, axis="y")
    fig.subplots_adjust(left=0.24 if not square else 0.28, right=0.98, top=0.86, bottom=0.12)
    _footer(fig)
    suffix = "_square" if square else ""
    _save(fig, Path(out) / f"wales_aurn_pm25_station_distribution_dark{suffix}")


def period_comparison_chart(comparison, out, square):
    fig, ax = _new(square)
    _header(
        ax,
        "PM₂.₅ in the recent dry period versus the preceding 70 days",
        "QC-screened station means; comparison is within station, not a Wales-wide average.",
    )
    work = comparison.dropna(subset=["previous_pm25_mean", "recent_pm25_mean"]).sort_values("pm25_change_pct")
    y_values = range(len(work))
    for y, row in zip(y_values, work.itertuples(index=False)):
        ax.plot([row.previous_pm25_mean, row.recent_pm25_mean], [y, y], color=GRID, linewidth=2, zorder=1)
        ax.scatter(row.previous_pm25_mean, y, s=70, color=MUTED, edgecolor=TEXT, linewidth=0.5, zorder=2)
        ax.scatter(row.recent_pm25_mean, y, s=90, color=CYAN, edgecolor=TEXT, linewidth=0.6, zorder=3)
        ax.text(
            max(row.previous_pm25_mean, row.recent_pm25_mean) + 0.18,
            y,
            f"{row.pm25_change_pct:+.0f}%",
            color=TEXT,
            fontsize=9,
            va="center",
        )
    ax.set_yticks(list(y_values))
    ax.set_yticklabels(work["station_name"].tolist(), color=MUTED)
    ax.set_xlabel("Mean daily PM₂.₅ (µg/m³)")
    ax.set_ylabel("")
    ax.grid(True, axis="x", color=GRID, alpha=0.38)
    ax.grid(False, axis="y")
    ax.scatter([], [], s=70, color=MUTED, edgecolor=TEXT, label="Previous 70 days")
    ax.scatter([], [], s=90, color=CYAN, edgecolor=TEXT, label="Recent 70 days")
    legend = ax.legend(loc="lower right", fontsize=8.5, facecolor=AX_BG, edgecolor=GRID)
    for text in legend.get_texts():
        text.set_color(TEXT)
    fig.subplots_adjust(left=0.24 if not square else 0.28, right=0.96, top=0.86, bottom=0.12)
    _footer(fig)
    suffix = "_square" if square else ""
    _save(fig, Path(out) / f"wales_aurn_pm25_recent_vs_previous_dark{suffix}")


def site_relative_chart(summary, out, square):
    fig, ax = _new(square)
    _header(
        ax,
        "Station-relative PM₂.₅: recent period versus preceding 70 days",
        "Residual = station PM₂.₅ minus same-day median of other AURN sites (≥4 peers). Not source apportionment.",
    )
    work = summary.dropna(subset=["previous_site_relative_mean", "recent_site_relative_mean"]).sort_values("site_relative_change")
    y_values = range(len(work))
    ax.axvline(0, color=MUTED, linewidth=1, alpha=0.8)
    for y, row in zip(y_values, work.itertuples(index=False)):
        ax.plot(
            [row.previous_site_relative_mean, row.recent_site_relative_mean],
            [y, y],
            color=GRID,
            linewidth=2,
        )
        ax.scatter(row.previous_site_relative_mean, y, s=70, color=MUTED, edgecolor=TEXT, linewidth=0.5)
        ax.scatter(row.recent_site_relative_mean, y, s=90, color=CYAN, edgecolor=TEXT, linewidth=0.6)
        ax.text(
            max(row.previous_site_relative_mean, row.recent_site_relative_mean) + 0.12,
            y,
            f"Δ {row.site_relative_change:+.2f}",
            color=TEXT,
            fontsize=9,
            va="center",
        )
    ax.set_yticks(list(y_values))
    ax.set_yticklabels(work["station_name"].tolist(), color=MUTED)
    ax.set_xlabel("Mean site-relative PM₂.₅ (µg/m³)")
    ax.set_ylabel("")
    ax.grid(True, axis="x", color=GRID, alpha=0.38)
    ax.grid(False, axis="y")
    fig.subplots_adjust(left=0.24 if not square else 0.28, right=0.96, top=0.86, bottom=0.12)
    _footer(fig)
    suffix = "_square" if square else ""
    _save(fig, Path(out) / f"wales_aurn_pm25_site_relative_change_dark{suffix}")


def july_event_chart(daily, out, square):
    fig, ax = _new(square)
    _header(
        ax,
        "Mid-July particulate episode and Blaenavon fire timeline",
        "QC-screened daily PM₂.₅, 13–24 July 2026. Fire-start marker is timeline context, not attribution.",
    )
    start = pd.Timestamp("2026-07-13", tz="UTC")
    end = pd.Timestamp("2026-07-24", tz="UTC")
    work = daily[daily["date"].between(start, end)].copy()
    value_col = "pm25_screened" if "pm25_screened" in work else "pm25"
    palette = _palette(work["station_name"].dropna().unique())
    for name, group in work.groupby("station_name"):
        valid = group.dropna(subset=[value_col])
        ax.plot(
            valid["date"],
            valid[value_col],
            marker="o",
            markersize=3,
            label=name,
            linewidth=1.6,
            color=palette[name],
        )
    fire = pd.Timestamp("2026-07-19", tz="UTC")
    ax.axvline(fire, color="#f59e0b", linestyle="--", linewidth=1.5)
    ax.text(
        fire + pd.Timedelta(hours=4),
        ax.get_ylim()[1] * 0.94,
        "Blaenavon fire\ninitial call 19 Jul",
        color="#f59e0b",
        fontsize=9,
        va="top",
    )
    ax.set_ylabel("Daily mean PM₂.₅ (µg/m³)")
    ax.set_xlabel("Date")
    ax.set_ylim(bottom=0)
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1 if not square else 2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    legend = ax.legend(
        loc="upper left",
        ncol=1 if square else 2,
        fontsize=8,
        facecolor=AX_BG,
        edgecolor=GRID,
    )
    for text in legend.get_texts():
        text.set_color(TEXT)
    fig.subplots_adjust(left=0.09, right=0.98, top=0.86, bottom=0.13)
    _footer(
        fig,
        "Air data: DEFRA UK-AIR AURN. Fire timeline: SWFRS initial call reported 19 Jul. Marker does not establish causation.",
    )
    suffix = "_square" if square else ""
    _save(fig, Path(out) / f"wales_aurn_pm25_july_event_screen_dark{suffix}")


def station_map(stations, out, square):
    fig, ax = _new(square)
    _header(
        ax,
        "Reference-grade PM₂.₅ monitoring sites used in Project 005",
        "Welsh AURN baseline stations; coordinates are sites, not a modelled pollution surface.",
    )
    types = sorted({station.site_type for station in stations})
    colors = ["#22d3ee", "#60a5fa", "#f59e0b", "#fb7185"]
    color_by_type = {site_type: colors[index % len(colors)] for index, site_type in enumerate(types)}
    for station in stations:
        ax.scatter(
            station.longitude,
            station.latitude,
            s=100 if square else 85,
            marker=SITE_TYPE_MARKERS.get(station.site_type, "o"),
            color=color_by_type[station.site_type],
            edgecolor=TEXT,
            linewidth=0.7,
            zorder=3,
            label=station.site_type,
        )
        ax.annotate(
            station.name,
            (station.longitude, station.latitude),
            xytext=(6, 6),
            textcoords="offset points",
            color=TEXT,
            fontsize=8.5,
        )
    handles, labels = ax.get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    legend = ax.legend(
        unique.values(),
        unique.keys(),
        loc="lower right",
        fontsize=8.5,
        facecolor=AX_BG,
        edgecolor=GRID,
    )
    for text in legend.get_texts():
        text.set_color(TEXT)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_xlim(-5.0, -2.4)
    ax.set_ylim(51.35, 53.25)
    fig.subplots_adjust(left=0.09, right=0.98, top=0.86, bottom=0.12)
    _footer(fig, "Source: DEFRA UK-AIR site metadata. Coordinates are monitoring-site locations.")
    suffix = "_square" if square else ""
    _save(fig, Path(out) / f"wales_aurn_pm25_station_map_dark{suffix}")


def render_all_charts(daily, hourly, stations, metadata, output_dir):
    sns.set_theme(context="notebook", style="darkgrid")
    output_dir = Path(output_dir)
    latest = pd.Timestamp(metadata["latest_observation_day_utc"])
    rolling_start = pd.Timestamp(metadata["rolling_start_utc"])
    recent_start = pd.Timestamp(metadata["recent_start_utc"])
    rolling = daily[daily["date"].between(rolling_start, latest)].copy()
    recent = daily[daily["date"].between(recent_start, latest)].copy()

    from analysis import (
        build_period_comparison,
        build_site_relative_daily,
        build_site_relative_summary,
    )

    comparison = build_period_comparison(daily, recent_start, latest, metadata["recent_days"])
    relative = build_site_relative_summary(
        build_site_relative_daily(daily), recent_start, latest, metadata["recent_days"]
    )
    rolling_subtitle = (
        f"QC-screened daily means, {rolling_start:%d %b %Y} to {latest:%d %b %Y}; "
        "≥18 valid hours per station-day."
    )
    recent_subtitle = (
        f"Recent {metadata['recent_days']}-day window, {recent_start:%d %b %Y} to "
        f"{latest:%d %b %Y}; observations only, no wildfire attribution."
    )
    for square in (False, True):
        suffix = "_square" if square else ""
        line_chart(
            rolling,
            output_dir,
            f"wales_aurn_pm25_rolling_year_dark{suffix}",
            "Measured PM₂.₅ across Wales: latest rolling year",
            rolling_subtitle,
            square,
        )
        line_chart(
            recent,
            output_dir,
            f"wales_aurn_pm25_recent_dark{suffix}",
            "Measured PM₂.₅ across Wales: recent dry-period window",
            recent_subtitle,
            square,
        )
        distribution_chart(rolling, output_dir, square)
        period_comparison_chart(comparison, output_dir, square)
        site_relative_chart(relative, output_dir, square)
        july_event_chart(daily, output_dir, square)
        station_map(stations, output_dir, square)
