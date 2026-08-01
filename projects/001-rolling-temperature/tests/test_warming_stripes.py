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


def test_warming_stripes_outputs_are_generated(tmp_path: Path) -> None:
    annual_path = tmp_path / "annual.csv"
    _annual_fixture().to_csv(annual_path, index=False)

    outputs = generate_warming_stripes(
        annual_path,
        pure_output_base=tmp_path / "pure",
        labelled_output_base=tmp_path / "labelled",
        data_output_path=tmp_path / "stripe_data.csv",
    )

    for path in (
        outputs.pure_png,
        outputs.pure_svg,
        outputs.labelled_png,
        outputs.labelled_svg,
        outputs.data_csv,
    ):
        assert path.exists()

    assert mpimg.imread(outputs.pure_png).shape[:2] == (900, 1600)
    assert mpimg.imread(outputs.labelled_png).shape[:2] == (900, 1600)

    labelled_svg = outputs.labelled_svg.read_text(encoding="utf-8")
    assert "WALES WARMING STRIPES" in labelled_svg
    assert "Professor Ed Hawkins" in labelled_svg
    assert "University of Reading" in labelled_svg
    assert "1961–2010" in labelled_svg
