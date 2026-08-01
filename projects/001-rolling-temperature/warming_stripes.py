"""Render Wales calendar-year warming stripes from validated Met Office data.

The visual approach follows Professor Ed Hawkins' warming-stripes model at the
University of Reading: one vertical stripe per calendar year, coloured by the
annual temperature anomaly relative to the 1961–2010 mean.

This module uses the official annual values already retained in
``data/derived/annual_reconciliation.csv``. It does not use the provisional
August-to-July scenario and does not alter the primary Project 001 analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, TwoSlopeNorm
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
    """Return a restrained 16-step blue-to-red warming-stripes palette."""

    return ListedColormap(sns.color_palette("RdBu_r", 16).as_hex())


def _save_stripes(
    data: pd.DataFrame,
    output_base: Path,
    *,
    labelled: bool,
) -> tuple[Path, Path]:
    """Save one-stripe-per-year PNG and SVG files."""

    anomalies = data["temperature_anomaly_c"].to_numpy(dtype=float)
    colour_limit = float(np.max(np.abs(anomalies)))
    if colour_limit == 0:
        colour_limit = 1.0

    norm = TwoSlopeNorm(vmin=-colour_limit, vcenter=0.0, vmax=colour_limit)
    cmap = _stripe_colormap()

    dpi = 100
    fig = plt.figure(
        figsize=(IMAGE_WIDTH_PX / dpi, IMAGE_HEIGHT_PX / dpi),
        dpi=dpi,
        facecolor="white",
    )

    if labelled:
        ax = fig.add_axes([0.06, 0.19, 0.88, 0.58])
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
            0.91,
            "WALES WARMING STRIPES",
            fontsize=28,
            fontweight="bold",
            ha="left",
            va="top",
        )
        fig.text(
            0.06,
            0.855,
            f"One stripe per calendar year, {first_year}–{last_year}",
            fontsize=16,
            ha="left",
            va="top",
        )
        fig.text(
            0.06,
            0.115,
            (
                f"Blue years were cooler and red years warmer than the {reference} "
                "Wales average."
            ),
            fontsize=12,
            ha="left",
            va="bottom",
        )
        fig.text(
            0.06,
            0.07,
            "Data: UK Met Office Wales annual mean temperature series.",
            fontsize=10,
            ha="left",
            va="bottom",
        )
        fig.text(
            0.06,
            0.04,
            (
                "Warming-stripes design: Professor Ed Hawkins, University of Reading "
                "(CC BY 4.0). Reproduction: Hinsawdd Cymru."
            ),
            fontsize=10,
            ha="left",
            va="bottom",
        )

    output_base.parent.mkdir(parents=True, exist_ok=True)
    png_path = output_base.with_suffix(".png")
    svg_path = output_base.with_suffix(".svg")
    fig.savefig(png_path, dpi=dpi, facecolor="white")
    fig.savefig(svg_path, facecolor="white")
    plt.close(fig)
    return png_path, svg_path


def generate_warming_stripes(
    annual_path: Path = ANNUAL_PATH,
    *,
    pure_output_base: Path = PURE_OUTPUT_BASE,
    labelled_output_base: Path = LABELLED_OUTPUT_BASE,
    data_output_path: Path = OUTPUT_DATA_PATH,
) -> StripeOutputs:
    """Create pure and labelled Wales calendar-year warming-stripes outputs."""

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
    return StripeOutputs(
        pure_png=pure_png,
        pure_svg=pure_svg,
        labelled_png=labelled_png,
        labelled_svg=labelled_svg,
        data_csv=data_output_path,
    )


def main() -> None:
    outputs = generate_warming_stripes()
    for name, path in outputs.__dict__.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
