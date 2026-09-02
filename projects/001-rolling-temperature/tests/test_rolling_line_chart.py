import json
from pathlib import Path
import sys

import matplotlib.image as mpimg
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from figure_style import (  # noqa: E402
    LABEL_REFERENCE_1991_2020,
    LABEL_ROLLING_WINDOWS,
    SQUARE_PX,
    STANDARD_HEIGHT_PX,
    STANDARD_WIDTH_PX,
)
from rolling_line_chart import prepare_chart_data, run  # noqa: E402


def _fixture(*, published: bool = True) -> pd.DataFrame:
    starts = pd.date_range("2024-01-01", periods=24, freq="MS")
    ends = starts + pd.DateOffset(months=11)
    values = [8.0 + index * 0.05 for index in range(len(starts))]
    statuses = ["published-inputs"] * len(starts)
    if not published:
        statuses[-1] = "provisional-scenario"
    return pd.DataFrame(
        {
            "start_month": starts,
            "end_month": ends,
            "period_label": [
                f"{start.strftime('%b %Y')} to {end.strftime('%b %Y')}"
                for start, end in zip(starts, ends)
            ],
            "mean_temperature_c": values,
            "days": [365] * len(starts),
            "status": statuses,
            "rank_warmest": list(range(len(starts), 0, -1)),
            "window_count": [len(starts)] * len(starts),
        }
    )


def _summary(*, published: bool = True) -> dict[str, object]:
    return {
        "derived_reference_1991_2020_c": 9.25,
        "source_last_updated": "01-Sep-2026 11:56",
        "last_published_month": "2026-08" if published else "2026-07",
    }


def test_prepare_chart_data_adds_smoothed_trend_and_metadata() -> None:
    chart, metadata = prepare_chart_data(_fixture(), _summary())

    assert "end_x" in chart.columns
    assert "smoothed_trend_c" in chart.columns
    assert metadata["latest_c"] == chart.iloc[-1]["mean_temperature_c"]
    assert metadata["latest_status"] == "published inputs"
    assert metadata["reference_mean_c"] == 9.25


def test_variants_generate_exact_dimensions(tmp_path: Path) -> None:
    source = tmp_path / "rolling.csv"
    summary_path = tmp_path / "summary.json"
    standard = tmp_path / "standard"
    dark = tmp_path / "dark"
    output_csv = tmp_path / "chart.csv"
    _fixture().to_csv(source, index=False)
    summary_path.write_text(json.dumps(_summary()), encoding="utf-8")

    outputs = run(source, summary_path, standard, dark, output_csv)

    assert mpimg.imread(outputs["standard_png"]).shape[:2] == (STANDARD_HEIGHT_PX, STANDARD_WIDTH_PX)
    assert mpimg.imread(outputs["dark_png"]).shape[:2] == (SQUARE_PX, SQUARE_PX)
    assert output_csv.exists()


def test_dark_svg_contains_rolling_legend_without_overlapping_latest_label() -> None:
    outputs = run()
    svg = outputs["dark_svg"].read_text(encoding="utf-8")

    assert LABEL_ROLLING_WINDOWS in svg
    assert LABEL_REFERENCE_1991_2020 in svg
    assert "Previous high" in svg
    assert "Latest published" not in svg
    assert "WALES: ROLLING 12-MONTH" in svg
