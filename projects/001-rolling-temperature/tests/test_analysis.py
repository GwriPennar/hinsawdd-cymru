from pathlib import Path
import sys

import pandas as pd
import pytest

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from analysis import (  # noqa: E402
    august_to_july_series,
    baseline_for_period,
    load_monthly_source,
    required_july_to_break_record,
    weighted_mean,
    with_july_2026,
)


def test_weighted_mean_uses_days_not_equal_month_weights() -> None:
    frame = pd.DataFrame(
        {
            "mean_temperature_c": [0.0, 10.0],
            "days": [31, 30],
        }
    )
    assert weighted_mean(frame) == pytest.approx(300 / 61)


def test_previous_august_to_july_record_is_2006_07() -> None:
    monthly = load_monthly_source()
    series = august_to_july_series(monthly)
    warmest = series.nlargest(1, "mean_temperature_c").iloc[0]
    assert warmest["period"] == "2006-08 to 2007-07"
    assert warmest["mean_temperature_c"] == pytest.approx(10.3150684932)


def test_july_break_even_is_well_below_record_july_temperature() -> None:
    monthly = load_monthly_source()
    previous = august_to_july_series(monthly).nlargest(1, "mean_temperature_c").iloc[0]
    required = required_july_to_break_record(monthly, float(previous["mean_temperature_c"]))
    assert required == pytest.approx(14.3290322581)


def test_central_scenario_is_new_august_to_july_record() -> None:
    monthly = with_july_2026(load_monthly_source(), 18.0, "provisional_central_estimate")
    series = august_to_july_series(monthly)
    current = series.loc[series["end_year"] == 2026].iloc[0]
    assert current["mean_temperature_c"] == pytest.approx(10.6268493151)
    assert current["rank_warmest"] == 1


def test_reference_baselines() -> None:
    monthly = load_monthly_source()
    assert baseline_for_period(monthly, 1961, 1990) == pytest.approx(8.6077558398)
    assert baseline_for_period(monthly, 1991, 2020) == pytest.approx(9.4184478332)
