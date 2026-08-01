from pathlib import Path
import sys

import matplotlib.image as mpimg
import pandas as pd
import pytest

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from warming_stripes import (  # noqa: E402
    generate_warming_stripes,
    prepare_stripe_data,
)


def _annual_fixture() -> pd.DataFrame:
    years = list(range(1950, 2012))
    temperatures = [8.0 + (year - 1950) * 0.02 for year in years]
    return pd.DataFrame(
        {
            "year": years,
            "official_annual_mean_c": temperatures,
        }
    )


def test_prepare_stripe_data_centres_reference_period() -> None:
    data = prepare_stripe_data(_annual_fixture())
    reference = data[data["year"].between(1961, 2010)]

    assert len(reference) == 50
    assert reference["temperature_anomaly_c"].mean() == pytest.approx(0.0)
    assert data["reference_period"].nunique() == 1
    assert data["reference_period"].iloc[0] == "1961–2010"


def test_climate_stripes_and_bars_outputs_are_generated(tmp_path: Path) -> None:
    annual_path = tmp_path / "annual.csv"
    _annual_fixture().to_csv(annual_path, index=False)

    outputs = generate_warming_stripes(
        annual_path,
        pure_output_base=tmp_path / "pure",
        labelled_output_base=tmp_path / "labelled",
        bars_output_base=tmp_path / "bars",
        bars_scale_output_base=tmp_path / "bars_with_scale",
        data_output_path=tmp_path / "stripe_data.csv",
    )

    for path in outputs.__dict__.values():
        assert path.exists()

    for path in (
        outputs.pure_png,
        outputs.labelled_png,
        outputs.bars_png,
        outputs.bars_with_scale_png,
    ):
        assert mpimg.imread(path).shape[:2] == (900, 1600)

    labelled_svg = outputs.labelled_svg.read_text(encoding="utf-8")
    assert "WALES WARMING STRIPES" in labelled_svg
    assert "Professor Ed Hawkins" in labelled_svg
    assert "University of Reading" in labelled_svg
    assert "1961–2010" in labelled_svg
    assert "Difference from 1961–2010 Wales average" in labelled_svg
    assert "Cooler" in labelled_svg
    assert "Warmer" in labelled_svg
    assert "Each stripe is one year" in labelled_svg

    bars_scale_svg = outputs.bars_with_scale_svg.read_text(encoding="utf-8")
    assert "WALES ANNUAL TEMPERATURE BARS" in bars_scale_svg
    assert "Difference from 1961–2010 average" in bars_scale_svg
    assert "One bar per calendar year" in bars_scale_svg
    assert "Cooler than 1961–2010 average" in bars_scale_svg
    assert "Warmer than 1961–2010 average" in bars_scale_svg
    assert "Bars below zero" in bars_scale_svg
    assert "Professor Ed Hawkins" in bars_scale_svg
