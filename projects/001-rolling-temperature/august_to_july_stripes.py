"""Render Wales August-to-July warming stripes and anomaly bars.

This presentation layer reads the validated, calendar-day-weighted equivalent-
period series produced by ``analysis.py``. It does not recalculate monthly means
or alter the retained Met Office source. The visual approach adapts Professor
Ed Hawkins' University of Reading climate-stripes model by moving the annual
boundary from January-December to August-July.
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
SOURCE_DATA_PATH = DERIVED_DIR / "august_to_july_mean_temperature.csv"
OUTPUT_DATA_PATH = DERIVED_DIR / "wales_august_to_july_warming_stripes.csv"
PURE_OUTPUT_BASE = FIGURES_DIR / "wales_august_to_july_warming_stripes"
EXPLAINED_OUTPUT_BASE = FIGURES_DIR / "wales_august_to_july_warming_stripes_explained"
BARS_OUTPUT_BASE = FIGURES_DIR / "wales_august_to_july_temperature_bars"
BARS_EXPLAINED_OUTPUT_BASE = (
    FIGURES_DIR / "wales_august_to_july_temperature_bars_explained"
)

REFERENCE_END_YEAR_START = 1961
REFERENCE_END_YEAR_END = 2010
ILLUSTRATIVE_JULY_2026_C = 18.0
IMAGE_WIDTH_PX = 1600
IMAGE_HEIGHT_PX = 900


@dataclass(frozen=True)
class AugustJulyGraphicOutputs:
    """Paths written by :func:`generate_august_to_july_graphics`."""

    pure_png: Path
    pure_svg: Path
    explained_png: Path
    explained_svg: Path
    bars_png: Path
    bars_svg: Path
    bars_explained_png: Path
    bars_explained_svg: Path
    data_csv: Path


def _period_label(start_year: int, end_year: int) -> str:
    """Return a compact label such as ``1884–85`` or ``1999–00``."""

    return f"{start_year}–{end_year % 100:02d}"


def _normalise_status(value: object) -> str:
    """Convert analysis status codes into reader-facing CSV values."""

    status = str(value).strip().lower().replace("_", "-")
    if status in {"published-inputs", "published inputs"}:
        return "published inputs"
    if status in {
        "provisional-scenario",
        "illustrative-scenario",
        "illustrative scenario",
    }:
        return "illustrative scenario"
    if not status:
        raise ValueError("August-to-July status must not be blank")
    return status.replace("-", " ")


def prepare_august_to_july_graphic_data(
    periods: pd.DataFrame,
    *,
    reference_end_year_start: int = REFERENCE_END_YEAR_START,
    reference_end_year_end: int = REFERENCE_END_YEAR_END,
) -> pd.DataFrame:
    """Validate equivalent periods and calculate the August-to-July anomaly.

    The reference mean is the arithmetic mean of the already day-weighted
    August-to-July period means whose end years run from 1961 through 2010,
    inclusive. This is an equivalent-period reference and is intentionally not
    copied from the calendar-year annual series.
    """

    required = {
        "period",
        "start_date",
        "end_date",
        "end_year",
        "mean_temperature_c",
        "status",
    }
    missing = required.difference(periods.columns)
    if missing:
        raise ValueError(f"Missing August-to-July columns: {sorted(missing)}")

    data = periods.loc[:, sorted(required)].copy()
    data["start_date"] = pd.to_datetime(data["start_date"], errors="raise")
    data["end_date"] = pd.to_datetime(data["end_date"], errors="raise")
    data["end_year"] = pd.to_numeric(data["end_year"], errors="raise").astype(int)
    data["mean_temperature_c"] = pd.to_numeric(
        data["mean_temperature_c"], errors="raise"
    )
    data["start_year"] = data["start_date"].dt.year.astype(int)
    data = data.sort_values(["start_date", "end_date"]).reset_index(drop=True)

    if data.empty:
        raise ValueError("August-to-July series is empty")
    if data[["start_date", "end_date", "end_year"]].duplicated().any():
        raise ValueError("August-to-July series contains duplicate periods")
    if data["mean_temperature_c"].isna().any():
        raise ValueError("August-to-July series contains missing means")

    starts_on_august_first = (
        (data["start_date"].dt.month == 8) & (data["start_date"].dt.day == 1)
    )
    if not starts_on_august_first.all():
        raise ValueError("Every equivalent period must begin on 1 August")
    if not (data["end_date"].dt.month == 7).all():
        raise ValueError("Every equivalent period must end in July")
    expected_month_end = data["end_date"] + pd.offsets.MonthEnd(0)
    if not data["end_date"].equals(expected_month_end):
        raise ValueError("Every equivalent period must end on the final day of July")
    if not (data["end_year"] == data["start_year"] + 1).all():
        raise ValueError("Every equivalent period must span consecutive years")

    expected_start_years = list(
        range(int(data["start_year"].min()), int(data["start_year"].max()) + 1)
    )
    if data["start_year"].tolist() != expected_start_years:
        raise ValueError("August-to-July periods contain gaps or duplicate start years")

    expected_end_years = [year + 1 for year in expected_start_years]
    if data["end_year"].tolist() != expected_end_years:
        raise ValueError("August-to-July periods contain gaps or duplicate end years")

    expected_periods = [
        f"{start_year:04d}-08 to {end_year:04d}-07"
        for start_year, end_year in zip(expected_start_years, expected_end_years)
    ]
    if data["period"].astype(str).tolist() != expected_periods:
        raise ValueError("August-to-July period identifiers are inconsistent")

    reference_mask = data["end_year"].between(
        reference_end_year_start, reference_end_year_end
    )
    expected_reference_count = reference_end_year_end - reference_end_year_start + 1
    reference = data.loc[reference_mask, "mean_temperature_c"]
    if len(reference) != expected_reference_count:
        raise ValueError(
            f"Reference must contain {expected_reference_count} complete "
            "August-to-July periods"
        )

    reference_mean = float(reference.mean())
    data["period_label"] = [
        _period_label(start_year, end_year)
        for start_year, end_year in zip(data["start_year"], data["end_year"])
    ]
    data["reference_period_definition"] = (
        f"August–July periods ending {reference_end_year_start}–"
        f"{reference_end_year_end}"
    )
    data["reference_mean_c"] = reference_mean
    data["temperature_anomaly_c"] = data["mean_temperature_c"] - reference_mean
    data["status"] = data["status"].map(_normalise_status)

    return data.loc[
        :,
        [
            "start_year",
            "end_year",
            "period_label",
            "mean_temperature_c",
            "reference_period_definition",
            "reference_mean_c",
            "temperature_anomaly_c",
            "status",
        ],
    ]


def _stripe_colormap() -> ListedColormap:
    """Return a restrained 16-step blue-to-red climate-stripes palette."""

    return ListedColormap(sns.color_palette("RdBu_r", 16).as_hex())


def _colour_scale(data: pd.DataFrame) -> tuple[ListedColormap, TwoSlopeNorm]:
    anomalies = data["temperature_anomaly_c"].to_numpy(dtype=float)
    colour_limit = float(np.max(np.abs(anomalies)))
    if not np.isfinite(colour_limit):
        raise ValueError("Temperature anomalies must be finite")
    if colour_limit == 0:
        colour_limit = 1.0
    return (
        _stripe_colormap(),
        TwoSlopeNorm(vmin=-colour_limit, vcenter=0.0, vmax=colour_limit),
    )


def _final_status_text(data: pd.DataFrame) -> str:
    label = str(data["period_label"].iloc[-1])
    status = str(data["status"].iloc[-1])
    if status == "illustrative scenario":
        return (
            f"{label}: PROVISIONAL — illustrative July 2026 scenario "
            f"({ILLUSTRATIVE_JULY_2026_C:.1f}°C)"
        )
    return f"{label}: published inputs"


def _save_figure(
    fig: plt.Figure,
    output_base: Path,
    *,
    dpi: int = 100,
) -> tuple[Path, Path]:
    output_base.parent.mkdir(parents=True, exist_ok=True)
    png_path = output_base.with_suffix(".png")
    svg_path = output_base.with_suffix(".svg")
    metadata = {
        "Title": output_base.name.replace("_", " "),
        "Creator": "Hinsawdd Cymru reproducible Python climate graphics",
    }
    fig.savefig(png_path, dpi=dpi, facecolor="white", metadata=metadata)
    fig.savefig(svg_path, facecolor="white", metadata=metadata)
    plt.close(fig)
    return png_path, svg_path


def _new_figure() -> tuple[plt.Figure, int]:
    dpi = 100
    fig = plt.figure(
        figsize=(IMAGE_WIDTH_PX / dpi, IMAGE_HEIGHT_PX / dpi),
        dpi=dpi,
        facecolor="white",
    )
    return fig, dpi


def _save_stripes(
    data: pd.DataFrame,
    output_base: Path,
    *,
    explained: bool,
) -> tuple[Path, Path]:
    anomalies = data["temperature_anomaly_c"].to_numpy(dtype=float)
    cmap, norm = _colour_scale(data)
    fig, dpi = _new_figure()

    if explained:
        ax = fig.add_axes([0.06, 0.405, 0.88, 0.30])
    else:
        ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])

    ax.imshow(
        anomalies[np.newaxis, :],
        aspect="auto",
        cmap=cmap,
        norm=norm,
        interpolation="nearest",
        extent=(-0.5, len(data) - 0.5, 0, 1),
    )
    ax.set_axis_off()

    if explained:
        first_label = str(data["period_label"].iloc[0])
        last_label = str(data["period_label"].iloc[-1])
        reference_definition = str(data["reference_period_definition"].iloc[0])
        reference_mean = float(data["reference_mean_c"].iloc[0])
        final_status = _final_status_text(data)

        fig.text(
            0.06,
            0.945,
            "WALES AUGUST–JULY WARMING STRIPES",
            fontsize=28,
            fontweight="bold",
            ha="left",
            va="top",
        )
        fig.text(
            0.06,
            0.885,
            (
                "Each stripe is one complete twelve-month period, from August to "
                f"the following July. {first_label} to {last_label}."
            ),
            fontsize=15,
            ha="left",
            va="top",
        )
        fig.text(
            0.06,
            0.835,
            final_status,
            fontsize=11.5,
            fontweight="bold" if "PROVISIONAL" in final_status else "normal",
            ha="left",
            va="top",
            bbox={
                "boxstyle": "round,pad=0.35",
                "facecolor": "#f7f7f7",
                "edgecolor": "#8a9099",
                "linewidth": 0.8,
            },
        )
        fig.text(0.06, 0.382, first_label, fontsize=10, ha="left", va="top")
        fig.text(0.94, 0.382, last_label, fontsize=10, ha="right", va="top")

        colourbar_ax = fig.add_axes([0.30, 0.285, 0.40, 0.026])
        mappable = ScalarMappable(norm=norm, cmap=cmap)
        mappable.set_array([])
        colourbar = fig.colorbar(
            mappable,
            cax=colourbar_ax,
            orientation="horizontal",
        )
        colourbar.set_label(
            "Temperature anomaly relative to the August–July reference (°C)",
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
        fig.text(0.275, 0.298, "Cooler", fontsize=9.5, ha="right", va="center")
        fig.text(0.725, 0.298, "Warmer", fontsize=9.5, ha="left", va="center")

        fig.text(
            0.06,
            0.218,
            (
                "Blue periods are cooler and red periods are warmer than the reference. "
                f"Reference: mean of {reference_definition} ({reference_mean:.2f}°C)."
            ),
            fontsize=10.8,
            ha="left",
            va="bottom",
        )
        fig.text(
            0.06,
            0.145,
            (
                "Source: Met Office National Climate Information Centre, Wales monthly "
                "mean air temperature series."
            ),
            fontsize=9.4,
            ha="left",
            va="bottom",
        )
        fig.text(
            0.06,
            0.095,
            (
                "Climate-stripes model: Professor Ed Hawkins, University of Reading "
                "(CC BY 4.0). Independent reproduction/adaptation: Hinsawdd Cymru."
            ),
            fontsize=9.4,
            ha="left",
            va="bottom",
        )
        fig.text(
            0.06,
            0.048,
            (
                "Adaptation note: the annual boundary is shifted from the usual "
                "January–December calendar year to complete August–July periods."
            ),
            fontsize=9.4,
            ha="left",
            va="bottom",
        )

    return _save_figure(fig, output_base, dpi=dpi)


def _save_bars(
    data: pd.DataFrame,
    output_base: Path,
    *,
    explained: bool,
) -> tuple[Path, Path]:
    anomalies = data["temperature_anomaly_c"].to_numpy(dtype=float)
    x = np.arange(len(data), dtype=float)
    cmap, norm = _colour_scale(data)
    colours = cmap(norm(anomalies))
    max_abs = float(np.max(np.abs(anomalies)))
    y_limit = max(0.5, np.ceil((max_abs + 0.05) * 10) / 10)

    fig, dpi = _new_figure()
    if explained:
        ax = fig.add_axes([0.09, 0.30, 0.86, 0.49])
    else:
        ax = fig.add_axes([0.025, 0.025, 0.95, 0.95])

    ax.bar(
        x,
        anomalies,
        width=1.0,
        align="center",
        color=colours,
        edgecolor=colours,
        linewidth=0,
    )
    ax.axhline(0.0, color="#30343b", linewidth=1.0, zorder=3)
    ax.set_xlim(-0.5, len(data) - 0.5)
    ax.set_ylim(-y_limit, y_limit)

    if explained:
        first_label = str(data["period_label"].iloc[0])
        last_label = str(data["period_label"].iloc[-1])
        reference_definition = str(data["reference_period_definition"].iloc[0])
        reference_mean = float(data["reference_mean_c"].iloc[0])
        final_status = _final_status_text(data)
        end_years = data["end_year"].to_numpy(dtype=int)

        anchor_years = [int(end_years[0])]
        anchor_years.extend(
            range(
                ((int(end_years[0]) + 19) // 20) * 20,
                int(end_years[-1]) + 1,
                20,
            )
        )
        if anchor_years[-1] != int(end_years[-1]):
            anchor_years.append(int(end_years[-1]))
        anchor_years = sorted(set(anchor_years))
        anchor_positions = [
            int(np.flatnonzero(end_years == year)[0]) for year in anchor_years
        ]

        ax.set_xticks(anchor_positions, [str(year) for year in anchor_years])
        ax.set_xlabel(
            "August–July period, labelled by end year", fontsize=12, labelpad=10
        )
        ax.set_ylabel("Temperature anomaly (°C)", fontsize=12, labelpad=10)
        ax.tick_params(axis="both", labelsize=10)
        ax.yaxis.grid(True, color="#d7dbe0", linewidth=0.8, alpha=0.8)
        ax.xaxis.grid(False)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["left", "bottom"]].set_color("#8a9099")
        ax.text(
            len(data) - 1.0,
            0.04 * y_limit,
            "0 = August–July reference mean",
            fontsize=9,
            ha="right",
            va="bottom",
            color="#30343b",
        )

        fig.text(
            0.09,
            0.945,
            "WALES AUGUST–JULY TEMPERATURE BARS",
            fontsize=27,
            fontweight="bold",
            ha="left",
            va="top",
        )
        fig.text(
            0.09,
            0.885,
            (
                f"Complete twelve-month periods from {first_label} to {last_label}. "
                "This is not a calendar-year chart."
            ),
            fontsize=15,
            ha="left",
            va="top",
        )
        fig.text(
            0.09,
            0.835,
            final_status,
            fontsize=11.5,
            fontweight="bold" if "PROVISIONAL" in final_status else "normal",
            ha="left",
            va="top",
        )

        legend_handles = [
            Patch(
                facecolor=cmap(norm(-max_abs)),
                edgecolor="none",
                label="Cooler than the August–July reference",
            ),
            Patch(
                facecolor=cmap(norm(max_abs)),
                edgecolor="none",
                label="Warmer than the August–July reference",
            ),
        ]
        fig.legend(
            handles=legend_handles,
            loc="lower left",
            bbox_to_anchor=(0.085, 0.172),
            ncol=2,
            frameon=False,
            fontsize=10,
            handlelength=1.8,
            columnspacing=2.4,
        )
        fig.text(
            0.09,
            0.145,
            (
                "Bar height shows how far each complete August–July period was above "
                f"or below the reference. Reference: {reference_definition} "
                f"({reference_mean:.2f}°C)."
            ),
            fontsize=10.2,
            ha="left",
            va="bottom",
        )
        fig.text(
            0.09,
            0.095,
            (
                "Source: Met Office National Climate Information Centre, Wales monthly "
                "mean air temperature series."
            ),
            fontsize=9.3,
            ha="left",
            va="bottom",
        )
        fig.text(
            0.09,
            0.050,
            (
                "Climate-stripes model: Professor Ed Hawkins, University of Reading "
                "(CC BY 4.0). Independent reproduction/adaptation: Hinsawdd Cymru. "
                "Annual boundary shifted to August–July."
            ),
            fontsize=9.3,
            ha="left",
            va="bottom",
        )
    else:
        ax.set_axis_off()

    return _save_figure(fig, output_base, dpi=dpi)


def generate_august_to_july_graphics(
    source_data_path: Path = SOURCE_DATA_PATH,
    *,
    pure_output_base: Path = PURE_OUTPUT_BASE,
    explained_output_base: Path = EXPLAINED_OUTPUT_BASE,
    bars_output_base: Path = BARS_OUTPUT_BASE,
    bars_explained_output_base: Path = BARS_EXPLAINED_OUTPUT_BASE,
    data_output_path: Path = OUTPUT_DATA_PATH,
) -> AugustJulyGraphicOutputs:
    """Generate all August-to-July stripes, bars and machine-readable data."""

    if not source_data_path.exists():
        raise FileNotFoundError(
            "Run analysis.py first so august_to_july_mean_temperature.csv is available"
        )

    periods = pd.read_csv(source_data_path)
    data = prepare_august_to_july_graphic_data(periods)
    data_output_path.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(data_output_path, index=False, float_format="%.6f")

    pure_png, pure_svg = _save_stripes(data, pure_output_base, explained=False)
    explained_png, explained_svg = _save_stripes(
        data, explained_output_base, explained=True
    )
    bars_png, bars_svg = _save_bars(data, bars_output_base, explained=False)
    bars_explained_png, bars_explained_svg = _save_bars(
        data, bars_explained_output_base, explained=True
    )

    return AugustJulyGraphicOutputs(
        pure_png=pure_png,
        pure_svg=pure_svg,
        explained_png=explained_png,
        explained_svg=explained_svg,
        bars_png=bars_png,
        bars_svg=bars_svg,
        bars_explained_png=bars_explained_png,
        bars_explained_svg=bars_explained_svg,
        data_csv=data_output_path,
    )


def main() -> None:
    """Build the retained August-to-July presentation assets."""

    outputs = generate_august_to_july_graphics()
    for name, path in outputs.__dict__.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
