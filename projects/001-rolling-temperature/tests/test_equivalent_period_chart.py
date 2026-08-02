import json
from pathlib import Path
import sys

import matplotlib.image as mpimg
import numpy as np
import pandas as pd
import pytest

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from equivalent_period_chart import (  # noqa: E402
    gaussian_smooth,
    load_inputs,
    prepare_chart_data,
    run,
)


def _period_fixture() -> pd.DataFrame:
    start_years = list(range(1884, 2026))
    end_years = [year + 1 for year in start_years]
    means = [7.2 + (index * 0.022) for index in range(len(start_years))]
    statuses = ["published-inputs"] * len(start_years)
    statuses[-1] = "provisional-scenario"
    return pd.DataFrame(
        {
            "period": [
                f"{start:04d}-08 to {end:04d}-07"
                for start, end in zip(start_years, end_years)
            ],
            "start_date": [f"{year:04d}-08-01" for year in start_years],
            "end_date": [f"{year:04d}-07-31" for year in end_years],
            "end_year": end_years,
            "mean_temperature_c": means,
            "days": [365] * len(start_years),
            "status": statuses,
            "rank_warmest": list(range(len(start_years), 0, -1)),
        }
    )


def _summary_fixture() -> dict[str, object]:
    return {
        "july_2026_value_used_c": 18.0,
        "source_last_updated": "01-Jul-2026 11:33",
    }


def test_gaussian_smoother_is_finite_and_deterministic() -> None:
    years = np.arange(1885, 1895, dtype=float)
    values = np.array([8.0, 7.5, 8.2, 8.1, 8.4, 8.0, 8.5, 8.7, 8.4, 8.9])

    first = gaussian_smooth(years, values, bandwidth_years=3.0)
    second = gaussian_smooth(years, values, bandwidth_years=3.0)

    assert np.isfinite(first).all()
    assert first == pytest.approx(second)
    assert first.min() >= values.min()
    assert first.max() <= values.max()


def test_prepare_chart_data_uses_equivalent_period_reference() -> None:
    chart, metadata = prepare_chart_data(_period_fixture(), _summary_fixture())
    reference = chart[chart["end_year"].between(1991, 2020)]
    published = chart[chart["status"] == "published-inputs"]

    assert chart.iloc[0]["period"] == "1884-08 to 1885-07"
    assert chart.iloc[-1]["period"] == "2025-08 to 2026-07"
    assert chart["end_year"].tolist() == list(range(1885, 2027))
    assert len(reference) == 30
    assert metadata["reference_mean_c"] == pytest.approx(
        reference["mean_temperature_c"].mean()
    )
    assert metadata["lowest_published_c"] == pytest.approx(
        published["mean_temperature_c"].min()
    )
    assert metadata["highest_published_c"] == pytest.approx(
        published["mean_temperature_c"].max()
    )
    assert metadata["latest_status"] == "illustrative scenario"
    assert chart["smoothed_trend_c"].notna().all()


def test_line_chart_outputs_dimensions_text_and_csv(tmp_path: Path) -> None:
    source_csv = tmp_path / "periods.csv"
    summary_json = tmp_path / "summary.json"
    output_base = tmp_path / "line_chart"
    output_csv = tmp_path / "line_chart.csv"
    _period_fixture().to_csv(source_csv, index=False)
    summary_json.write_text(json.dumps(_summary_fixture()), encoding="utf-8")

    outputs = run(
        source_csv=source_csv,
        summary_json=summary_json,
        output_basename=output_base,
        output_csv=output_csv,
    )

    for path in outputs.values():
        assert path.exists()
    assert mpimg.imread(outputs["png"]).shape[:2] == (900, 1600)

    svg = outputs["svg"].read_text(encoding="utf-8")
    assert "WALES AUGUST–JULY MEAN TEMPERATURE" in svg
    assert "Complete twelve-month periods, 1884–85 to 2025–26" in svg
    assert "1991–2020 equivalent-period reference" in svg
    assert "lowest published period" in svg
    assert "highest published period" in svg
    assert "latest 2025–26" in svg
    assert "smoothed trend" in svg
    assert "Met Office Wales HadUK-Grid series" in svg
    assert "Independent reproduction" in svg
    assert "illustrative scenario" in svg
    assert "not a published or endorsed Met Office value" in svg

    output_data = pd.read_csv(outputs["csv"])
    assert output_data.iloc[0]["period"] == "1884-08 to 1885-07"
    assert output_data.iloc[-1]["period"] == "2025-08 to 2026-07"
    assert output_data["smoothed_trend_c"].notna().all()


def test_retained_project_result_is_unchanged() -> None:
    data, summary = load_inputs()
    chart, metadata = prepare_chart_data(data, summary)

    assert chart.iloc[-1]["mean_temperature_c"] == pytest.approx(10.626849)
    assert chart.iloc[-1]["status"] == "provisional-scenario"
    assert metadata["latest_status"] == "illustrative scenario"
    assert metadata["july_2026_value_c"] == pytest.approx(18.0)
    assert metadata["reference_mean_c"] == pytest.approx(
        float(summary["derived_reference_1991_2020_c"])
    )


def test_load_inputs_rejects_gaps(tmp_path: Path) -> None:
    source_csv = tmp_path / "periods.csv"
    summary_json = tmp_path / "summary.json"
    _period_fixture().drop(index=4).to_csv(source_csv, index=False)
    summary_json.write_text(json.dumps(_summary_fixture()), encoding="utf-8")

    with pytest.raises(ValueError, match="continuous"):
        load_inputs(source_csv, summary_json)
