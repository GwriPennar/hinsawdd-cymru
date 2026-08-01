from pathlib import Path
import sys

import pandas as pd
import pytest

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from analysis import (  # noqa: E402
    annual_reconciliation,
    august_to_july_series,
    load_source,
    reference_value_for_target_sequence,
    required_july_to_break_record,
    weighted_mean,
    with_july_2026,
)


def test_weighted_mean_uses_days_not_equal_month_weights() -> None:
    frame = pd.DataFrame({"mean_temperature_c": [0.0, 10.0], "days": [31, 30]})
    assert weighted_mean(frame) == pytest.approx(300 / 61)


def test_previous_august_to_july_record_is_2006_07() -> None:
    bundle = load_source()
    series = august_to_july_series(bundle.monthly)
    warmest = series.nlargest(1, "mean_temperature_c").iloc[0]
    assert warmest["period"] == "2006-08 to 2007-07"
    assert warmest["mean_temperature_c"] == pytest.approx(10.3150684932)


def test_july_break_even_is_well_below_record_july_temperature() -> None:
    bundle = load_source()
    previous = august_to_july_series(bundle.monthly).nlargest(1, "mean_temperature_c").iloc[0]
    required = required_july_to_break_record(bundle.monthly, float(previous["mean_temperature_c"]))
    assert required == pytest.approx(14.3290322581)


def test_central_scenario_is_new_august_to_july_record() -> None:
    bundle = load_source()
    monthly = with_july_2026(bundle.monthly, 18.0, "provisional_scenario")
    series = august_to_july_series(monthly)
    current = series.loc[series["end_year"] == 2026].iloc[0]
    assert current["mean_temperature_c"] == pytest.approx(10.6268493151)
    assert current["rank_warmest"] == 1


def test_reference_values_are_plausible_and_complete() -> None:
    monthly = load_source().monthly
    old = reference_value_for_target_sequence(monthly, 1961, 1990)
    new = reference_value_for_target_sequence(monthly, 1991, 2020)
    assert old == pytest.approx(8.61, abs=0.03)
    assert new == pytest.approx(9.42, abs=0.03)
    assert new > old


def test_official_annual_reconciliation_when_available() -> None:
    reconciliation = annual_reconciliation(load_source())
    if reconciliation.empty:
        pytest.skip("Legacy normalized snapshot does not retain the official annual column")
    assert reconciliation["absolute_difference_c"].max() <= 0.06
