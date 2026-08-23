"""Dark-mode Stage A charts for Wales coastal SST (HadISST monthly)."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import TwoSlopeNorm

from constants import (
    BLUE,
    COOL,
    CYAN,
    DERIVED_DIR,
    FIGURES_DIR,
    HOT,
    MUTED,
    RAW_DIR,
    SERIES_CHART_YEARS,
    TEXT,
    WARM,
)
from style import finish, new_figure, new_figure_panels


def _load_series(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    df["date"] = pd.to_datetime(df["date"], utc=True)
    return df.set_index("date").sort_index()


def render_history(series: pd.DataFrame, *, output_dir: Path = FIGURES_DIR) -> list[Path]:
    end = series.index.max()
    start = end - pd.DateOffset(years=SERIES_CHART_YEARS)
    window = series.loc[series.index >= start]
    paths: list[Path] = []
    for square in (False, True):
        fig, axes = new_figure_panels(square=square, nrows=2, height_ratios=(2.6, 1.0))
        ax, ax_a = axes
        ax.plot(window.index, window["sst_c"], color=CYAN, lw=1.6, label="Wales shelf SST")
        ax.plot(window.index, window["clim_sst_c"], color=BLUE, lw=1.1, alpha=0.85, label="1991–2020 clim.")
        ax.set_ylabel("SST (°C)")
        ax.set_title("Wales shelf sea-surface temperature (monthly)", color=TEXT, fontsize=16 if not square else 14, pad=10)
        ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
        colors = np.where(window["anomaly_c"].to_numpy() >= 0, WARM, COOL)
        ax_a.bar(window.index, window["anomaly_c"], color=colors, width=20, alpha=0.85)
        ax_a.axhline(0, color=MUTED, lw=0.8)
        ax_a.set_ylabel("Anomaly (°C)")
        out = output_dir / ("wales_shelf_sst_history_dark" + ("_square" if square else ""))
        finish(
            fig,
            out,
            square=square,
            source_note=(
                "Met Office HadISST1 monthly · Wales shelf box mean · anomaly vs 1991–2020 · "
                "Hinsawdd Cymru Project 007 Stage A · analysis SST, not a thermometer reading"
            ),
        )
        paths.append(out.with_suffix(".png"))
    return paths


def render_anomaly_map(grid: pd.DataFrame, latest_date: str, *, output_dir: Path = FIGURES_DIR) -> list[Path]:
    paths: list[Path] = []
    pivot = grid.pivot_table(index="latitude", columns="longitude", values="anomaly_c")
    vmax = float(np.nanmax(np.abs(pivot.values))) if np.isfinite(pivot.values).any() else 1.0
    vmax = max(0.5, min(5.0, vmax))
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0.0, vmax=vmax)
    for square in (False, True):
        fig, ax = new_figure(square=square)
        mesh = ax.pcolormesh(
            pivot.columns.values,
            pivot.index.values,
            pivot.values,
            cmap="RdBu_r",
            norm=norm,
            shading="auto",
        )
        cb = fig.colorbar(mesh, ax=ax, fraction=0.046, pad=0.04)
        cb.set_label("SST anomaly (°C)", color=MUTED)
        cb.ax.yaxis.set_tick_params(color=MUTED)
        plt.setp(plt.getp(cb.ax.axes, "yticklabels"), color=MUTED)
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_title(f"Wales shelf SST anomaly · {latest_date}", color=TEXT, fontsize=15 if not square else 13, pad=10)
        out = output_dir / ("wales_shelf_sst_anomaly_map_dark" + ("_square" if square else ""))
        finish(
            fig,
            out,
            square=square,
            source_note="Met Office HadISST1 · Hinsawdd Cymru Project 007 Stage A · monthly analysis SST",
        )
        paths.append(out.with_suffix(".png"))
    return paths


def render_enso_context(series: pd.DataFrame, oni: pd.DataFrame, *, output_dir: Path = FIGURES_DIR) -> list[Path]:
    end = series.index.max()
    start = end - pd.DateOffset(years=SERIES_CHART_YEARS)
    window = series.loc[series.index >= start]
    oni = oni.copy()
    oni["date"] = pd.to_datetime(oni["date"], utc=True)
    oni_w = oni.loc[oni["date"] >= start]
    paths: list[Path] = []
    for square in (False, True):
        fig, axes = new_figure_panels(square=square, nrows=2, height_ratios=(2.2, 1.2))
        ax, ax_o = axes
        ax.plot(window.index, window["anomaly_c"], color=CYAN, lw=1.4)
        ax.axhline(0, color=MUTED, lw=0.8)
        ax.set_ylabel("Wales SST anomaly (°C)")
        ax.set_title("Wales shelf SST anomaly with Pacific ENSO context", color=TEXT, fontsize=15 if not square else 13, pad=10)
        ax_o.fill_between(
            oni_w["date"],
            0,
            oni_w["oni"],
            where=oni_w["oni"].to_numpy() >= 0,
            color=HOT,
            alpha=0.55,
            interpolate=True,
            label="ONI ≥ 0",
        )
        ax_o.fill_between(
            oni_w["date"],
            0,
            oni_w["oni"],
            where=oni_w["oni"].to_numpy() < 0,
            color=COOL,
            alpha=0.55,
            interpolate=True,
            label="ONI < 0",
        )
        ax_o.axhline(0.5, color=WARM, lw=0.7, ls="--", alpha=0.7)
        ax_o.axhline(-0.5, color=COOL, lw=0.7, ls="--", alpha=0.7)
        ax_o.set_ylabel("ONI (°C)")
        ax_o.legend(loc="upper left", fontsize=8, ncol=2, framealpha=0.9)
        out = output_dir / ("wales_shelf_sst_enso_context_dark" + ("_square" if square else ""))
        finish(
            fig,
            out,
            square=square,
            source_note=(
                "Wales anomaly: Met Office HadISST1 vs 1991–2020 · ONI: NOAA CPC · "
                "ENSO is Pacific context only — not a claim that El Niño drives Welsh shelf SST · "
                "Hinsawdd Cymru Project 007"
            ),
        )
        paths.append(out.with_suffix(".png"))
    return paths


def render_all(
    *,
    derived_dir: Path = DERIVED_DIR,
    raw_dir: Path = RAW_DIR,
    output_dir: Path = FIGURES_DIR,
) -> dict:
    series = _load_series(derived_dir / "wales_shelf_sst_monthly.csv")
    grid = pd.read_csv(derived_dir / "wales_shelf_sst_anomaly_grid_latest.csv")
    oni = pd.read_csv(raw_dir / "oni.csv")
    summary = json.loads((derived_dir / "summary.json").read_text())
    latest = summary.get("latest_date", str(series.index.max().date()))
    paths: list[Path] = []
    paths += render_history(series, output_dir=output_dir)
    paths += render_anomaly_map(grid, latest, output_dir=output_dir)
    paths += render_enso_context(series, oni, output_dir=output_dir)
    return {"figures": [str(p) for p in paths]}


def main() -> int:
    print(json.dumps(render_all(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
