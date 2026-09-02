from pathlib import Path
import sys

import matplotlib.image as mpimg

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from analysis import AnalysisConfig, run  # noqa: E402
from figure_style import (  # noqa: E402
    LABEL_INDIVIDUAL_PERIODS,
    LABEL_REFERENCE_1991_2020,
    LABEL_TRAILING_AVERAGE,
    SQUARE_PX,
    STANDARD_HEIGHT_PX,
    STANDARD_WIDTH_PX,
)
from line_chart_variants import run as run_line_variants  # noqa: E402


def test_make_figure_svg_contains_three_legend_entries() -> None:
    run(AnalysisConfig(), update_project_readme=False)
    svg = (
        PROJECT_DIR
        / "figures/wales_august_to_july_mean_temperature_provisional.svg"
    ).read_text(encoding="utf-8")

    assert LABEL_INDIVIDUAL_PERIODS in svg
    assert LABEL_TRAILING_AVERAGE in svg
    assert LABEL_REFERENCE_1991_2020 in svg
    assert "10-window" not in svg


def test_main_trend_uses_trailing_10_year_average_label() -> None:
    run(AnalysisConfig(), update_project_readme=False)
    svg = (
        PROJECT_DIR
        / "figures/wales_august_to_july_mean_temperature_provisional.svg"
    ).read_text(encoding="utf-8")

    assert LABEL_TRAILING_AVERAGE in svg
    assert "Trailing 10-window average" not in svg


def test_dark_line_chart_previous_high_uses_prior_record_not_current() -> None:
    outputs = run_line_variants()
    dark_svg = outputs.dark_svg.read_text(encoding="utf-8")

    assert "Previous high" in dark_svg
    assert "2006–07  10.32" in dark_svg
    previous_idx = dark_svg.index("Previous high")
    latest_idx = dark_svg.index("2025–26")
    assert previous_idx < latest_idx
    assert dark_svg[previous_idx:latest_idx].count("10.61") == 0


def test_line_chart_variant_dimensions_match_style_guide() -> None:
    outputs = run_line_variants()

    assert mpimg.imread(outputs.standard_png).shape[:2] == (STANDARD_HEIGHT_PX, STANDARD_WIDTH_PX)
    assert mpimg.imread(outputs.dark_png).shape[:2] == (SQUARE_PX, SQUARE_PX)
