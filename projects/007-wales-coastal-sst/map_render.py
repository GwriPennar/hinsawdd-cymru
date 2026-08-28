"""Shared SST map rendering helpers for Project 007."""
from __future__ import annotations

import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.colors import Normalize, TwoSlopeNorm
from matplotlib.patches import Rectangle

from constants import (
    PANEL_BG,
    WALES_LAT_MAX,
    WALES_LAT_MIN,
    WALES_LON_MAX,
    WALES_LON_MIN,
)


def thin_grid(grid: pd.DataFrame, *, step: int = 3) -> pd.DataFrame:
    """Subsample lat/lon for lighter SVG output."""
    if step <= 1 or len(grid) <= 5000:
        return grid
    lat_keep = sorted(grid["latitude"].unique())[::step]
    lon_keep = sorted(grid["longitude"].unique())[::step]
    return grid[grid["latitude"].isin(lat_keep) & grid["longitude"].isin(lon_keep)].copy()


def grid_to_pivot(grid: pd.DataFrame, value_col: str) -> pd.DataFrame:
    return grid.pivot_table(index="latitude", columns="longitude", values=value_col)


def draw_wales_box(ax: Axes, *, color: str = "#f8fafc", lw: float = 1.0, alpha: float = 0.85) -> None:
    rect = Rectangle(
        (WALES_LON_MIN, WALES_LAT_MIN),
        WALES_LON_MAX - WALES_LON_MIN,
        WALES_LAT_MAX - WALES_LAT_MIN,
        fill=False,
        edgecolor=color,
        linewidth=lw,
        linestyle="--",
        alpha=alpha,
    )
    ax.add_patch(rect)


def draw_sst_map(
    ax: Axes,
    grid: pd.DataFrame,
    *,
    value_col: str,
    cmap: str,
    norm: Normalize | TwoSlopeNorm,
    lon_min: float,
    lon_max: float,
    lat_min: float,
    lat_max: float,
    show_wales_box: bool = False,
) -> object:
    pivot = grid_to_pivot(grid, value_col)
    lons = pivot.columns.values
    lats = pivot.index.values
    lon_edges = np.concatenate(
        [[lons[0] - (lons[1] - lons[0]) / 2], (lons[:-1] + lons[1:]) / 2, [lons[-1] + (lons[-1] - lons[-2]) / 2]]
    )
    lat_edges = np.concatenate(
        [[lats[0] - (lats[1] - lats[0]) / 2], (lats[:-1] + lats[1:]) / 2, [lats[-1] + (lats[-1] - lats[-2]) / 2]]
    )
    mesh = ax.pcolormesh(lon_edges, lat_edges, pivot.values, cmap=cmap, norm=norm, shading="flat")
    ax.set_xlim(lon_min, lon_max)
    ax.set_ylim(lat_min, lat_max)
    ax.set_aspect("equal", adjustable="box")
    ax.set_facecolor(PANEL_BG)
    if show_wales_box:
        draw_wales_box(ax)
    return mesh
