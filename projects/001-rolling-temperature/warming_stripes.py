"""Render Wales calendar-year warming stripes and bars from validated data.

The visual approach follows Professor Ed Hawkins' climate-stripes model at the
University of Reading: one vertical mark per calendar year, coloured by the
annual temperature anomaly relative to the 1961–2010 mean.

This module uses the official annual values already retained in
``data/derived/annual_reconciliation.csv``. It does not use the provisional
August-to-July scenario and does not alter the primary Project 001 analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from matplotlib.cm import ScalarMappable
from matplotlib.colors import ListedColormap, TwoSlopeNorm
from matplotlib.patches import Patch
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

PROJECT_DIR = Path(__file__).resolve().parent
DERIVED_DIR = PROJECT_DIR / "data/derived"
FIGURES_DIR = PROJECT_DIR / "figures"
ANNUAL_PATH = DERIVED_DIR / "annual_reconciliation.csv"
OUTPUT_DATA_PATH = DERIVED_DIR / "wales_calendar_year_warming_stripes.csv"
PURE_OUTPUT_BASE = FIGURES_DIR / "wales_calendar_year_warming_stripes"
LABELLED_OUTPUT_BASE = FIGURES_DIR / "wales_calendar_year_warming_stripes_labelled"
BARS_OUTPUT_BASE = FIGURES_DIR / "wales_calendar_year_temperature_bars"
BARS_SCALE_OUTPUT_BASE = FIGURES_DIR / "wales_calendar_year_temperature_bars_with_scale"

REFERENCE_START = 1961
REFERENCE_END = 2010
IMAGE_WIDTH_PX = 1600
IMAGE_HEIGHT_PX = 900


@dataclass(frozen=True)
class StripeOutputs:
    pure_png: Path
    pure_svg: Path
    labelled_png: Path
    labelled_svg: Path
    bars_png: Path
    bars_svg: Path
    bars_with_scale_png: Path
    bars_with_scale_svg: Path
    data_csv: Path


def prepare_stripe_data(
    annual: pd.DataFrame,
    *,
    reference_start: int = REFERENCE_START,
    reference_end: int = REFERENCE_END,
) -> pd.DataFrame:
    """Validate official annual values and calculate reference-period anomalies."""

    required = {"year", "official_annual_mean_c"}
    missing = required.difference(annual.columns)
    if missing:
        raise ValueError(f"Missing annual columns: {sorted(missing)}")

    data = annual.loc[:, ["year", "official_annual_mean_c"]].copy()
    data["year"] = pd.to_numeric(data["year"], errors="raise").astype(int)
    data["official_annual_mean_c"] = pd.to_numeric(
        data["official_annual_mean_c"], errors="raise"
    )
    data = data.dropna().sort_values("year").reset_index(drop=True)

    if data.empty:
        raise ValueError("Annual series is empty")
    if data["year"].duplicated().any():
        raise ValueError("Annual series contains duplicate years")

    expected = list(range(int(data["year"].min()), int(data["year"].max()) + 1))
    if data["year"].tolist() != expected:
        raise ValueError("Annual series contains missing calendar years")

    reference = data.loc[
        data["year"].between(reference_start, reference_end),
        "official_annual_mean_c",
    ]
    expected_reference_years = reference_end - reference_start + 1
    if len(reference) != expected_reference_years:
        raise ValueError(
            f"Reference period must contain {expected_reference_years} complete years"
        )

    reference_mean = float(reference.mean())
    data["reference_period"] = f"{reference_start}–{reference_end}"
    data["reference_mean_c"] = reference_mean
    data["temperature_anomaly_c"] = data["official_annual_mean_c"] - reference_mean
    return data


def _stripe_colormap() -> ListedColormap:
    """Return a restrained 16-step blue-to-red climate-stripes palette."""

    return ListedColormap(sns.color_palette("RdBu_r", 16).as_hex())


def _colour_scale(data: pd.DataFrame) -> tuple[ListedColormap, TwoSlopeNorm]:
    anomalies = data["temperature_anomaly_c"].to_numpy(dtype=float)
    colour_limit = float(np.max(np.abs(anomalies)))
    if colour_limit == 0:
        colour_limit = 1.0
    return (
        _stripe_colormap(),
        TwoSlopeNorm(vmin=-colour_limit, vcenter=0.0, vmax=colour_limit),
    )


def _save_figure(
    fig: plt.Figure,
    output_base: Path,
    *,
    dpi: int = 100,
) -> tuple[Path, Path]:
    output_base.parent.mkdir(parents=True, exist_ok=True)
    png_path = output_base.with_suffix(".png")
    svg_path = output_base.with_suffix(".svg")
    fig.savefig(png_path, dpi=dpi, facecolor="white")
    fig.savefig(svg_path, facecolor="white")
    plt.close(fig)
    return png_path, svg_path


def _save_stripes(
    data: pd.DataFrame,
    output_base: Path,
    *,
    labelled: bool,
) -> tuple[Path, Path]:
    """Save one-stripe-per-year PNG and SVG files."""

    anomalies = data["temperature_anomaly_c"].to_numpy(dtype=float)
    cmap, norm = _colour_scale(data)

    dpi = 100
    fig = plt.figure(
        figsize=(IMAGE_WIDTH_PX / dpi, IMAGE_HEIGHT_PX / dpi),
        dpi=dpi,
        facecolor="white",
    )

    if labelled:
        ax = fig.add_axes([0.06, 0.31, 0.88, 0.43])
    else:
        ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])

    ax.imshow(
        anomalies[np.newaxis, :],
        aspect="auto",
        cmap=cmap,
        norm=norm,
        interpolation="nearest",
        extent=(
            float(data["year"].min()) - 0.5,
            float(data["year"].max()) + 0.5,
            0,
            1,
        ),
    )
    ax.set_axis_off()

    if labelled:
        first_year = int(data["year"].min())
        last_year = int(data["year"].max())
        reference = str(data["reference_period"].iloc[0])

        fig.text(
            0.06,
            0.93,
            "WALES WARMING STRIPES",
            fontsize=28,
            fontweight="bold",
            ha="left",
            va="top",
        )
        fig.text(
            0.06,
            0.872,
            (
                f"One stripe per calendar year, {first_year}–{last_year}. "
                f"Colour shows the difference from the {reference} Wales average."
            ),
            fontsize=15,
            ha="left",
            va="top",
        )
        fig.text(0.06, 0.285, str(first_year), fontsize=10, ha="left", va="top")
        fig.text(0.94, 0.285, str(last_year), fontsize=10, ha="right", va="top")

        colourbar_ax = fig.add_axes([0.30, 0.205, 0.40, 0.025])
        mappable = ScalarMappable(norm=norm, cmap=cmap)
        mappable.set_array([])
        colourbar = fig.colorbar(
            mappable,
            cax=colourbar_ax,
            orientation="horizontal",
        )
        colourbar.set_label(
            f"Difference from {reference} Wales average (°C)",
            fontsize=10,
            labelpad=5,
        )
        ticks = [float(norm.vmin), 0.0, float(norm.vmax)]
        colourbar.set_ticks(ticks)
        colourbar.set_ticklabels(
            [f"{ticks[0]:.1f}", "0", f"+{ticks[2]:.1f}"]
        )
        colourbar.ax.tick_params(labelsize=9, length=3)
        colourbar.outline.set_edgecolor("#8a9099")
        fig.text(0.275, 0.218, "Cooler", fontsize=9.5, ha="right", va="center")
        fig.text(0.725, 0.218, "Warmer", fontsize=9.5, ha="left", va="center")

        fig.text(
            0.06,
            0.125,
            "Each stripe is one year. The sequence moves from cooler blues towards warmer reds in recent decades.",
            fontsize=11,
            ha="left",
            va="bottom",
        )
        fig.text(
            0.06,
            0.075,
            "Data: UK Met Office Wales annual mean temperature series.",
            fontsize=9.5,
            ha="left",
            va="bottom",
        )
        fig.text(
            0.06,
            0.04,
            (
                "Climate-stripes design: Professor Ed Hawkins, University of Reading "
                "(CC BY 4.0). Reproduction: Hinsawdd Cymru."
            ),
            fontsize=9.5,
            ha="left",
            va="bottom",
        )

    return _save_figure(fig, output_base, dpi=dpi)


def _save_bars(
    data: pd.DataFrame,
    output_base: Path,
    *,
    with_scale: bool,
) -> tuple[Path, Path]:
    """Save variable-height annual anomaly bars, with or without chart furniture."""

    years = data["year"].to_numpy(dtype=int)
    anomalies = data["temperature_anomaly_c"].to_numpy(dtype=float)
    cmap, norm = _colour_scale(data)
    colours = cmap(norm(anomalies))

    max_abs = float(np.max(np.abs(anomalies)))
    y_limit = max(0.5, np.ceil((max_abs + 0.05) * 10) / 10)
    first_year = int(years.min())
    last_year = int(years.max())
    reference = str(data["reference_period"].iloc[0])

    dpi = 100
    fig = plt.figure(
        figsize=(IMAGE_WIDTH_PX / dpi, IMAGE_HEIGHT_PX / dpi),
        dpi=dpi,
        facecolor="white",
    )

    if with_scale:
        ax = fig.add_axes([0.09, 0.28, 0.86, 0.53])
    else:
        ax = fig.add_axes([0.025, 0.025, 0.95, 0.95])

    ax.bar(
        years,
        anomalies,
        width=1.0,
        align="center",
        color=colours,
        edgecolor=colours,
        linewidth=0,
    )
    ax.axhline(0.0, color="#30343b", linewidth=1.0, zorder=3)
    ax.set_xlim(first_year - 0.5, last_year + 0.5)
    ax.set_ylim(-y_limit, y_limit)

    if with_scale:
        tick_years = [first_year]
        tick_years.extend(
            range(((first_year + 19) // 20) * 20, last_year + 1, 20)
        )
        if tick_years[-1] != last_year:
            tick_years.append(last_year)
        tick_years = sorted(set(tick_years))

        ax.set_xticks(tick_years)
        ax.set_xlabel("Calendar year", fontsize=12, labelpad=10)
        ax.set_ylabel(
            f"Difference from {reference} average (°C)",
            fontsize=12,
            labelpad=10,
        )
        ax.tick_params(axis="both", labelsize=10)
        ax.yaxis.grid(True, color="#d7dbe0", linewidth=0.8, alpha=0.8)
        ax.xaxis.grid(False)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["left", "bottom"]].set_color("#8a9099")

        fig.text(
            0.09,
            0.93,
            "WALES ANNUAL TEMPERATURE BARS",
            fontsize=27,
            fontweight="bold",
            ha="left",
            va="top",
        )
        fig.text(
            0.09,
            0.872,
            (
                f"One bar per calendar year, {first_year}–{last_year}. "
                f"Height shows the difference from the {reference} Wales average."
            ),
            fontsize=15,
            ha="left",
            va="top",
        )

        legend_handles = [
            Patch(
                facecolor=cmap(norm(-max_abs)),
                edgecolor="none",
                label=f"Cooler than {reference} average",
            ),
            Patch(
                facecolor=cmap(norm(max_abs)),
                edgecolor="none",
                label=f"Warmer than {reference} average",
            ),
        ]
        fig.legend(
            handles=legend_handles,
            loc="lower left",
            bbox_to_anchor=(0.085, 0.145),
            ncol=2,
            frameon=False,
            fontsize=10,
            handlelength=1.8,
            columnspacing=2.4,
        )
        fig.text(
            0.09,
            0.115,
            "Bars below zero are cooler than the reference average; bars above zero are warmer.",
            fontsize=10.5,
            ha="left",
            va="bottom",
        )
        fig.text(
            0.09,
            0.07,
            "Data: UK Met Office Wales annual mean temperature series.",
            fontsize=9.5,
            ha="left",
            va="bottom",
        )
        fig.text(
            0.09,
            0.035,
            (
                "Climate-stripes model: Professor Ed Hawkins, University of Reading "
                "(CC BY 4.0). Reproduction: Hinsawdd Cymru."
            ),
            fontsize=9.5,
            ha="left",
            va="bottom",
        )
    else:
        ax.set_axis_off()

    return _save_figure(fig, output_base, dpi=dpi)


def generate_warming_stripes(
    annual_path: Path = ANNUAL_PATH,
    *,
    pure_output_base: Path = PURE_OUTPUT_BASE,
    labelled_output_base: Path = LABELLED_OUTPUT_BASE,
    bars_output_base: Path = BARS_OUTPUT_BASE,
    bars_scale_output_base: Path = BARS_SCALE_OUTPUT_BASE,
    data_output_path: Path = OUTPUT_DATA_PATH,
) -> StripeOutputs:
    """Create stripes, anomaly bars and their labelled Wales outputs."""

    if not annual_path.exists():
        raise FileNotFoundError(
            "Run analysis.py first so annual_reconciliation.csv is available"
        )

    annual = pd.read_csv(annual_path)
    data = prepare_stripe_data(annual)
    data_output_path.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(data_output_path, index=False, float_format="%.6f")

    pure_png, pure_svg = _save_stripes(data, pure_output_base, labelled=False)
    labelled_png, labelled_svg = _save_stripes(
        data,
        labelled_output_base,
        labelled=True,
    )
    bars_png, bars_svg = _save_bars(
        data,
        bars_output_base,
        with_scale=False,
    )
    bars_with_scale_png, bars_with_scale_svg = _save_bars(
        data,
        bars_scale_output_base,
        with_scale=True,
    )
    return StripeOutputs(
        pure_png=pure_png,
        pure_svg=pure_svg,
        labelled_png=labelled_png,
        labelled_svg=labelled_svg,
        bars_png=bars_png,
        bars_svg=bars_svg,
        bars_with_scale_png=bars_with_scale_png,
        bars_with_scale_svg=bars_with_scale_svg,
        data_csv=data_output_path,
    )


def main() -> None:
    outputs = generate_warming_stripes()
    for name, path in outputs.__dict__.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
