from pathlib import Path
import sys

import matplotlib.image as mpimg

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from figure_style import (  # noqa: E402
    LABEL_REFERENCE_1991_2020,
    LABEL_ROLLING_AVERAGE,
    LABEL_ROLLING_WINDOWS,
    SQUARE_PX,
)
from monthly_monitor import run  # noqa: E402


def test_rolling_history_svg_contains_three_legend_entries() -> None:
    outputs = run()
    svg = outputs["history_svg"].read_text(encoding="utf-8")

    assert LABEL_ROLLING_WINDOWS in svg
    assert LABEL_ROLLING_AVERAGE in svg
    assert LABEL_REFERENCE_1991_2020 in svg
    assert "August-to-July" not in svg


def test_rolling_dark_square_svg_contains_three_legend_entries() -> None:
    outputs = run()
    svg = outputs["dark_svg"].read_text(encoding="utf-8")

    assert LABEL_ROLLING_WINDOWS in svg
    assert LABEL_ROLLING_AVERAGE in svg
    assert LABEL_REFERENCE_1991_2020 in svg


def test_rolling_monitor_dimensions_match_style_guide() -> None:
    outputs = run()
    dark = mpimg.imread(outputs["dark_png"])

    assert dark.shape[:2] == (SQUARE_PX, SQUARE_PX)
