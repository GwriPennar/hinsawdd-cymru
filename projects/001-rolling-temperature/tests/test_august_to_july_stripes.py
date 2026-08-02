from pathlib import Path
import sys

import matplotlib.image as mpimg
import pandas as pd
import pytest

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from august_to_july_stripes import (  # noqa: E402
    generate_august_to_july_graphics,
    prepare_august_to_july_graphic_data,
)


def _period_fixture() -> pd.DataFrame:
    start_years = list(range(1884, 2026))
    end_years = [year + 1 for year in start_years]
    means = [7.0 + (index * 0.025) for index in range(len(start_years))]
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
            "status": statuses,
        }
    )


def test_prepare_august_to_july_data_is_continuous_and_centred() -> None:
    data = prepare_august_to_july_graphic_data(_period_fixture())
    reference = data[data["end_year"].between(1961, 2010)]

    assert data["period_label"].iloc[0] == "1884–85"
    assert data["period_label"].iloc[-1] == "2025–26"
    assert data["start_year"].tolist() == list(range(1884, 2026))
    assert data["end_year"].tolist() == list(range(1885, 2027))
    assert not data["period_label"].duplicated().any()
    assert len(reference) == 50
    assert reference["temperature_anomaly_c"].mean() == pytest.approx(0.0)
    assert (
        data["reference_period_definition"].iloc[0]
        == "August–July periods ending 1961–2010"
    )
    assert data["status"].iloc[-1] == "illustrative scenario"


def test_august_to_july_graphics_and_svg_explanations(tmp_path: Path) -> None:
    source_path = tmp_path / "periods.csv"
    _period_fixture().to_csv(source_path, index=False)

    outputs = generate_august_to_july_graphics(
        source_path,
        pure_output_base=tmp_path / "stripes",
        explained_output_base=tmp_path / "stripes_explained",
        bars_output_base=tmp_path / "bars",
        bars_explained_output_base=tmp_path / "bars_explained",
        data_output_path=tmp_path / "graphic_data.csv",
    )

    for path in outputs.__dict__.values():
        assert path.exists()

    for path in (
        outputs.pure_png,
        outputs.explained_png,
        outputs.bars_png,
        outputs.bars_explained_png,
    ):
        assert mpimg.imread(path).shape[:2] == (900, 1600)

    graphic_data = pd.read_csv(outputs.data_csv)
    assert graphic_data.columns.tolist() == [
        "start_year",
        "end_year",
        "period_label",
        "mean_temperature_c",
        "reference_period_definition",
        "reference_mean_c",
        "temperature_anomaly_c",
        "status",
    ]

    explained_svg = outputs.explained_svg.read_text(encoding="utf-8")
    assert "WALES AUGUST–JULY WARMING STRIPES" in explained_svg
    assert "Temperature anomaly relative to the August–July reference (°C)" in explained_svg
    assert "August–July periods ending 1961–2010" in explained_svg
    assert "Met Office National Climate Information Centre" in explained_svg
    assert "Professor Ed Hawkins" in explained_svg
    assert "University of Reading" in explained_svg
    assert "Hinsawdd Cymru" in explained_svg
    assert "2025–26: PROVISIONAL" in explained_svg

    bars_svg = outputs.bars_explained_svg.read_text(encoding="utf-8")
    assert "WALES AUGUST–JULY TEMPERATURE BARS" in bars_svg
    assert "Temperature anomaly (°C)" in bars_svg
    assert "Cooler than the August–July reference" in bars_svg
    assert "Warmer than the August–July reference" in bars_svg
    assert "0 = August–July reference mean" in bars_svg
    assert "above or below the reference" in bars_svg
    assert "2025–26: PROVISIONAL" in bars_svg


def test_retained_project_result_is_unchanged() -> None:
    source_path = PROJECT_DIR / "data/derived/august_to_july_mean_temperature.csv"
    data = prepare_august_to_july_graphic_data(pd.read_csv(source_path))

    assert data["period_label"].iloc[0] == "1884–85"
    assert data["period_label"].iloc[-1] == "2025–26"
    assert data["mean_temperature_c"].iloc[-1] == pytest.approx(10.626849)
    assert data["status"].iloc[-1] == "illustrative scenario"


def test_rejects_missing_or_duplicate_periods() -> None:
    periods = _period_fixture().drop(index=5).reset_index(drop=True)
    with pytest.raises(ValueError, match="gaps or duplicate"):
        prepare_august_to_july_graphic_data(periods)

    duplicated = pd.concat([_period_fixture(), _period_fixture().iloc[[0]]])
    with pytest.raises(ValueError, match="duplicate periods"):
        prepare_august_to_july_graphic_data(duplicated)
