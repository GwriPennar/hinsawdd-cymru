#!/usr/bin/env python3
"""11 August 2026 physical-clock PM2.5 event screen for Project 005."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

FIG_BG = "#080c16"
AX_BG = "#0f172a"
TEXT = "#f8fafc"
MUTED = "#94a3b8"
GRID = "#334155"
EVENT_START = pd.Timestamp("2026-08-11 00:00", tz="UTC")
EVENT_END = EVENT_START + pd.Timedelta(days=1)
CHART_END = pd.Timestamp("2026-08-11 12:00", tz="UTC")
PRIOR_DAYS = 365


def load_hourly(path: Path) -> pd.DataFrame:
    hourly = pd.read_csv(path)
    hourly["timestamp"] = pd.to_datetime(hourly["timestamp"], utc=True)
    if "reporting_date" in hourly:
        hourly["reporting_date"] = pd.to_datetime(hourly["reporting_date"], utc=True)
    for column in ("pm25", "pm25_screened", "pm10", "no2"):
        if column in hourly:
            hourly[column] = pd.to_numeric(hourly[column], errors="coerce")
    return hourly


def build_aug11_event_summary(hourly: pd.DataFrame) -> pd.DataFrame:
    """Compare physical-clock 11 Aug hours with each station's prior-year hourly PM2.5."""
    prior_start = EVENT_START - pd.Timedelta(days=PRIOR_DAYS)
    rows = []
    for (code, name, site_type), group in hourly.groupby(
        ["station_code", "station_name", "site_type"], dropna=False
    ):
        value_column = "pm25_screened" if "pm25_screened" in group else "pm25"
        history = pd.to_numeric(
            group[
                group["timestamp"].between(prior_start, EVENT_START, inclusive="left")
            ][value_column],
            errors="coerce",
        ).dropna()
        event = group[
            group["timestamp"].between(EVENT_START, EVENT_END, inclusive="left")
        ].copy()
        event["pm25_event"] = pd.to_numeric(event[value_column], errors="coerce")
        valid = event.dropna(subset=["pm25_event"])
        if valid.empty:
            continue
        p95 = float(history.quantile(0.95)) if len(history) else None
        max_index = valid["pm25_event"].idxmax()
        pm10 = pd.to_numeric(valid.get("pm10"), errors="coerce")
        no2 = pd.to_numeric(valid.get("no2"), errors="coerce")
        ratio = valid["pm25_event"] / pm10
        ratio = ratio.where(pm10.gt(0)).dropna()
        rows.append(
            {
                "station_code": code,
                "station_name": name,
                "site_type": site_type,
                "valid_hours": int(len(valid)),
                "event_pm25_mean": float(valid["pm25_event"].mean()),
                "event_pm25_max": float(valid["pm25_event"].max()),
                "event_pm25_max_timestamp_utc": valid.loc[
                    max_index, "timestamp"
                ].isoformat(),
                "prior_365d_hourly_pm25_p95": p95,
                "hours_at_or_above_prior_p95": (
                    int((valid["pm25_event"] >= p95).sum()) if p95 is not None else None
                ),
                "event_pm10_mean": float(pm10.mean()),
                "event_no2_mean": float(no2.mean()),
                "event_mean_pm25_to_pm10_ratio": float(ratio.mean()),
            }
        )
    return (
        pd.DataFrame(rows)
        .sort_values("event_pm25_mean", ascending=False)
        .reset_index(drop=True)
    )


def write_event_outputs(hourly: pd.DataFrame, derived_dir: Path) -> pd.DataFrame:
    derived_dir.mkdir(parents=True, exist_ok=True)
    columns = [
        "timestamp",
        "reporting_date",
        "station_code",
        "station_name",
        "site_type",
        "pm25",
        "pm25_screened",
        "pm10",
        "no2",
        "pm25_status",
        "pm10_status",
    ]
    available = [column for column in columns if column in hourly.columns]
    event = hourly[
        hourly["timestamp"].between(EVENT_START, EVENT_END, inclusive="left")
    ][available].copy()
    event.to_csv(derived_dir / "pm25_aug11_hourly.csv", index=False)
    summary = build_aug11_event_summary(hourly)
    summary.to_csv(derived_dir / "pm25_aug11_event_summary.csv", index=False)
    return summary


def _apply_dark(ax):
    ax.set_facecolor(AX_BG)
    ax.tick_params(colors=MUTED, labelsize=9)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.grid(True, color=GRID, alpha=0.38, linewidth=0.7)
    ax.set_axisbelow(True)
    ax.xaxis.label.set_color(MUTED)
    ax.yaxis.label.set_color(MUTED)


def _palette(names):
    colours = [
        "#22d3ee",
        "#60a5fa",
        "#a78bfa",
        "#f59e0b",
        "#fb7185",
        "#f43f5e",
        "#34d399",
    ]
    return {name: colours[index % len(colours)] for index, name in enumerate(sorted(names))}


def render_event_chart(hourly: pd.DataFrame, output_base: Path, square: bool = False) -> None:
    figsize = (10.8, 10.8) if square else (16, 9)
    fig, ax = plt.subplots(figsize=figsize, dpi=100)
    fig.patch.set_facecolor(FIG_BG)
    _apply_dark(ax)
    ax.set_title(
        "11 August 2026 overnight particulate window",
        loc="left",
        color=TEXT,
        fontsize=20,
        fontweight="bold",
        pad=24,
    )
    ax.text(
        0,
        1.015,
        "Hourly QC-screened PM₂.₅, GMT hour ending. Swansea coverage stops after 05:00; no source attribution.",
        transform=ax.transAxes,
        color=MUTED,
        fontsize=10,
        va="bottom",
    )
    work = hourly[
        hourly["timestamp"].between(EVENT_START, CHART_END, inclusive="both")
    ].copy()
    value_column = "pm25_screened" if "pm25_screened" in work else "pm25"
    work[value_column] = pd.to_numeric(work[value_column], errors="coerce")
    palette = _palette(work["station_name"].dropna().unique())
    for name, group in work.groupby("station_name"):
        valid = group.dropna(subset=[value_column])
        if valid.empty:
            continue
        swansea = name == "Swansea Roadside"
        ax.plot(
            valid["timestamp"],
            valid[value_column],
            marker="o",
            markersize=5 if swansea else 3,
            linewidth=2.8 if swansea else 1.3,
            alpha=1.0 if swansea else 0.75,
            label=name,
            color=palette[name],
            zorder=5 if swansea else 2,
        )
    ax.axvline(EVENT_START, color=MUTED, linewidth=1, linestyle="--", alpha=0.8)
    ax.text(
        EVENT_START + pd.Timedelta(minutes=10),
        0.96,
        "midnight GMT",
        transform=ax.get_xaxis_transform(),
        color=MUTED,
        fontsize=8,
        va="top",
    )
    ax.set_ylabel("Hourly PM₂.₅ (µg/m³)")
    ax.set_xlabel("11 August 2026, GMT hour ending")
    ax.set_ylim(bottom=0)
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=2 if square else 1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    legend = ax.legend(
        loc="upper right",
        ncol=1 if square else 2,
        fontsize=8,
        facecolor=AX_BG,
        edgecolor=GRID,
    )
    for text in legend.get_texts():
        text.set_color(TEXT)
    fig.subplots_adjust(left=0.09, right=0.98, top=0.86, bottom=0.13)
    fig.text(
        0.01,
        0.012,
        "Source: DEFRA UK-AIR AURN. Swansea has six physical-clock PM₂.₅ observations from 00:00–05:00 GMT; later hours are missing.",
        color=MUTED,
        fontsize=8,
        ha="left",
        va="bottom",
    )
    output_base.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_base.with_suffix(".png"), dpi=100, facecolor=FIG_BG, bbox_inches=None)
    fig.savefig(output_base.with_suffix(".svg"), facecolor=FIG_BG, bbox_inches=None)
    plt.close(fig)


def main() -> None:
    project_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--hourly",
        type=Path,
        default=project_dir / "data" / "derived" / "aurn_hourly_combined.csv",
    )
    parser.add_argument(
        "--derived-dir", type=Path, default=project_dir / "data" / "derived"
    )
    parser.add_argument(
        "--figures-dir", type=Path, default=project_dir / "figures"
    )
    args = parser.parse_args()
    hourly = load_hourly(args.hourly)
    summary = write_event_outputs(hourly, args.derived_dir)
    stem = "wales_aurn_pm25_aug11_smoke_window_dark"
    render_event_chart(hourly, args.figures_dir / stem, square=False)
    render_event_chart(hourly, args.figures_dir / f"{stem}_square", square=True)
    print(summary.to_csv(index=False))


if __name__ == "__main__":
    main()
