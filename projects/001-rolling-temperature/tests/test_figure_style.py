from pathlib import Path
import sys

import matplotlib.image as mpimg

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from analysis import AnalysisConfig, make_figure, run  # noqa: E402
from figure_style import (  # noqa: E402
    LABEL_INDIVIDUAL_PERIODS,
    LABEL_REFERENCE_1991_2020,
    LABEL_ROLLING_AVERAGE,
    LABEL_ROLLING_WINDOWS,
    SQUARE_PX,
    STANDARD_HEIGHT_PX,
    STANDARD_WIDTH_PX,
)
from line_chart_variants import run as run_line_variants  # noqa: E402
from monthly_monitor import run as run_monthly_monitor  # noqa: E402


def test_rolling_history_svg_contains_three_legend_entries() -> None:
    run(AnalysisConfig(), update_project_readme=False)
    run_monthly_monitor()
    svg = (
        PROJECT_DIR
        / "figures/wales_rolling_12_month_temperature_history.svg"
    ).read_text(encoding="utf-8")

    assert LABEL_ROLLING_WINDOWS in svg
    assert LABEL_ROLLING_AVERAGE in svg
    assert LABEL_REFERENCE_1991_2020 in svg
    assert "August-to-July" not in svg


def test_archived_august_july_make_figure_legend_entries(tmp_path: Path) -> None:
    import pandas as pd

    from source_data import load_source

    august_july = __import__("calculations", fromlist=["august_to_july_series"]).august_to_july_series(
        load_source().monthly
    )
    output = tmp_path / "provisional"
    make_figure(august_july, output, 17.8, "published-inputs", 9.42)
    svg = output.with_suffix(".svg").read_text(encoding="utf-8")
    assert LABEL_INDIVIDUAL_PERIODS in svg
    assert "Trailing 10-year average" in svg
    assert LABEL_REFERENCE_1991_2020 in svg


def test_dark_line_chart_previous_high_uses_prior_record_not_current() -> None:
    outputs = run_line_variants()
    dark_svg = outputs.dark_svg.read_text(encoding="utf-8")

    assert "Previous high" in dark_svg
    assert "2006–07  10.32" in dark_svg
    previous_idx = dark_svg.index("Previous high")
    latest_idx = dark_svg.index("2025–26")
    assert previous_idx < latest_idx
    assert dark_svg[previous_idx:latest_idx].count("10.61") == 0


def test_rolling_dark_line_chart_previous_high_uses_prior_window() -> None:
    run(AnalysisConfig(), update_project_readme=False)
    outputs = run_monthly_monitor()
    dark_svg = outputs["dark_svg"].read_text(encoding="utf-8")
    assert LABEL_ROLLING_WINDOWS in dark_svg

    line_dark = outputs["line_dark_svg"].read_text(encoding="utf-8")
    assert "Previous high" in line_dark
    assert "May 2006 to Apr 2007" in line_dark


def test_line_chart_variant_dimensions_match_style_guide() -> None:
    run(AnalysisConfig(), update_project_readme=False)
    outputs = run_monthly_monitor()

    assert mpimg.imread(outputs["line_standard_png"]).shape[:2] == (STANDARD_HEIGHT_PX, STANDARD_WIDTH_PX)
    assert mpimg.imread(outputs["dark_png"]).shape[:2] == (SQUARE_PX, SQUARE_PX)
    assert mpimg.imread(outputs["line_dark_png"]).shape[:2] == (SQUARE_PX, SQUARE_PX)
