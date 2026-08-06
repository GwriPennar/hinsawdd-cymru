"""Build the joined rainfall, July, rain-day and continuation analysis."""

from __future__ import annotations

import numpy as np
import pandas as pd

from dark_climate_constants import SourceBundle
from dark_climate_stats import (bootstrap_projection, fit_linear, fit_theil_sen, monthly_reference, rolling_august_to_july)

def build_analysis(rainfall: SourceBundle, raindays: SourceBundle) -> dict[str, object]:
    rainfall_reference_monthly = monthly_reference(rainfall.monthly)
    rain_reference = float(rainfall_reference_monthly.sum())
    rainfall_periods = rolling_august_to_july(rainfall.monthly, value_name="rainfall_total_mm")
    rainfall_periods["reference_1991_2020_mm"] = rain_reference
    rainfall_periods["percentage_of_1991_2020"] = rainfall_periods["rainfall_total_mm"] / rain_reference * 100.0
    rainfall_periods["anomaly_percent"] = rainfall_periods["percentage_of_1991_2020"] - 100.0
    rainfall_periods["trailing_10_period_mean_mm"] = rainfall_periods["rainfall_total_mm"].rolling(10, min_periods=10).mean()
    rainfall_periods["trailing_10_period_anomaly_percent"] = rainfall_periods["anomaly_percent"].rolling(10, min_periods=10).mean()

    july = rainfall.monthly[rainfall.monthly["month"] == 7][["year", "value"]].rename(columns={"value": "july_rainfall_mm"}).copy()
    july_reference = float(rainfall_reference_monthly.loc[7])
    july["reference_1991_2020_mm"] = july_reference
    july["percentage_of_1991_2020"] = july["july_rainfall_mm"] / july_reference * 100.0
    july["trailing_10_year_mean_mm"] = july["july_rainfall_mm"].rolling(10, min_periods=10).mean()
    july["dryness_rank"] = july["july_rainfall_mm"].rank(method="min", ascending=True).astype(int)

    rainday_reference_monthly = monthly_reference(raindays.monthly)
    rainday_reference = float(rainday_reference_monthly.sum())
    rainday_periods = rolling_august_to_july(raindays.monthly, value_name="rain_days_ge_1mm")
    rainday_periods["reference_1991_2020_days"] = rainday_reference
    rainday_periods["anomaly_days"] = rainday_periods["rain_days_ge_1mm"] - rainday_reference
    rainday_periods["trailing_10_period_mean_days"] = rainday_periods["rain_days_ge_1mm"].rolling(10, min_periods=10).mean()

    modern = rainfall_periods[rainfall_periods["end_year"] >= 1970].copy()
    primary = fit_linear(modern["end_year"], modern["rainfall_total_mm"])
    full = fit_linear(rainfall_periods["end_year"], rainfall_periods["rainfall_total_mm"])
    robust = fit_theil_sen(modern["end_year"], modern["rainfall_total_mm"])
    projection_years = np.arange(primary.last_year, 2101)
    lower, upper = bootstrap_projection(modern, projection_years)
    projection = pd.DataFrame(
        {
            "end_year": projection_years.astype(int),
            "primary_projection_mm": primary.predict(projection_years),
            "bootstrap_95_lower_mm": lower,
            "bootstrap_95_upper_mm": upper,
            "full_record_sensitivity_mm": full.predict(projection_years),
            "theil_sen_sensitivity_mm": robust.predict(projection_years),
        }
    )
    return {
        "rainfall_periods": rainfall_periods,
        "july": july,
        "rainday_periods": rainday_periods,
        "projection": projection,
        "fits": {"primary": primary, "full": full, "robust": robust},
        "rainfall_reference_mm": rain_reference,
        "july_reference_mm": july_reference,
        "rainday_reference_days": rainday_reference,
    }
