import json
from pathlib import Path
import sys

import matplotlib.image as mpimg
import numpy as np
import pandas as pd
import pytest

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from model import (  # noqa: E402
    ModelConfig,
    fit_linear_trend,
    load_validated_inputs,
    moving_block_bootstrap,
    prepare_projection,
    run,
    theil_sen_fit,
)


def _synthetic_data() -> pd.DataFrame:
    years = np.arange(1885, 2027)
    values = 8.0 + 0.02 * (years - 1885)
    statuses = ["published-inputs"] * len(years)
    statuses[-1] = "provisional-scenario"
    return pd.DataFrame(
        {
            "period": [f"{year - 1}-08 to {year}-07" for year in years],
            "start_date": [f"{year - 1}-08-01" for year in years],
            "end_date": [f"{year}-07-31" for year in years],
            "end_year": years,
            "mean_temperature_c": values,
            "days": [365] * len(years),
            "status": statuses,
            "rank_warmest": list(range(len(years), 0, -1)),
            "temperature_anomaly_c": values - 9.0,
        }
    )


def _summary() -> dict[str, object]:
    return {
        "derived_reference_1991_2020_c": 9.0,
        "source_snapshot_sha256": "abc",
        "source_last_updated": "01-Jul-2026 11:33",
        "period_mean_central_c": float(
            _synthetic_data().iloc[-1].mean_temperature_c
        ),
        "rank_among_august_to_july_periods": 1,
    }


def test_ols_and_theil_sen_recover_linear_slope() -> None:
    data = _synthetic_data()
    published = data[
        (data.status == "published-inputs") & (data.end_year >= 1970)
    ]
    ols = fit_linear_trend(published)
    robust = theil_sen_fit(published)

    assert ols.slope_c_per_year == pytest.approx(0.02)
    assert robust.slope_c_per_year == pytest.approx(0.02)
    assert ols.r_squared == pytest.approx(1.0)


def test_bootstrap_is_deterministic() -> None:
    data = _synthetic_data()
    published = data[
        (data.status == "published-inputs") & (data.end_year >= 1970)
    ]
    config = ModelConfig(bootstrap_replicates=100, random_seed=7)
    years = np.arange(2025, 2031)

    first = moving_block_bootstrap(published, years, config)
    second = moving_block_bootstrap(published, years, config)
    for first_array, second_array in zip(first, second):
        assert first_array == pytest.approx(second_array)


def test_prepare_projection_excludes_provisional_point() -> None:
    data = _synthetic_data()
    config = ModelConfig(bootstrap_replicates=100, projection_end_year=2100)
    projection, summary, backtests = prepare_projection(data, _summary(), config)

    assert summary["latest_context_used_for_training"] is False
    assert summary["primary_fit"]["last_end_year"] == 2025
    assert summary["primary_fit"]["observation_count"] == 56
    assert projection.end_year.iloc[-1] == 2100
    assert len(backtests) == 4


def test_retained_project_inputs_and_outputs(tmp_path: Path) -> None:
    data, summary, verification = load_validated_inputs()
    assert verification["verification_status"] == "pass"
    assert data.iloc[-1]["mean_temperature_c"] == pytest.approx(10.626849)
    assert data.iloc[-1]["status"] == "provisional-scenario"

    original_readme = PROJECT_DIR / "README.md"
    readme_copy = tmp_path / "README.md"
    readme_copy.write_text(
        original_readme.read_text(encoding="utf-8"), encoding="utf-8"
    )

    import model

    old_derived = model.DERIVED_DIR
    old_figures = model.FIGURES_DIR
    old_readme = model.README_PATH
    model.DERIVED_DIR = tmp_path / "data/derived"
    model.FIGURES_DIR = tmp_path / "figures"
    model.README_PATH = readme_copy
    try:
        result = run(ModelConfig(bootstrap_replicates=100))
    finally:
        model.DERIVED_DIR = old_derived
        model.FIGURES_DIR = old_figures
        model.README_PATH = old_readme

    assert result["primary_fit"]["last_end_year"] == 2025
    assert result["latest_context_mean_c"] == pytest.approx(10.626849)
    assert result["milestones"]["2050"][
        "primary_mean_temperature_c"
    ] == pytest.approx(10.651908, abs=1e-5)
    assert result["milestones"]["2100"][
        "primary_mean_temperature_c"
    ] == pytest.approx(12.031080, abs=1e-5)
    image = mpimg.imread(
        tmp_path / "figures/wales_temperature_pathways_linear_regression.png"
    )
    assert image.shape[:2] == (900, 1600)
    generated_readme = readme_copy.read_text(encoding="utf-8")
    assert "This is not a physical climate forecast" in generated_readme
    assert "10.65°C" in generated_readme


def test_load_inputs_rejects_failed_verification(tmp_path: Path) -> None:
    data = _synthetic_data().drop(columns=["temperature_anomaly_c"])
    source = tmp_path / "data.csv"
    summary_path = tmp_path / "summary.json"
    verification_path = tmp_path / "verification.json"
    data.to_csv(source, index=False)
    summary_path.write_text(json.dumps(_summary()), encoding="utf-8")
    verification_path.write_text(
        json.dumps(
            {
                "verification_status": "fail",
                "primary_summary_comparison": "pass",
                "source_sha256": "abc",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="verification has not passed"):
        load_validated_inputs(source, summary_path, verification_path)
