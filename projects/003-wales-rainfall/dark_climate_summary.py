"""Build the machine-readable Project 003 headline summary."""

from __future__ import annotations

import pandas as pd

from dark_climate_constants import LinearFit, SourceBundle


def build_summary(analysis: dict[str, object], rainfall: SourceBundle, raindays: SourceBundle) -> dict[str, object]:
    rainfall_periods: pd.DataFrame = analysis["rainfall_periods"]
    july: pd.DataFrame = analysis["july"]
    rainday_periods: pd.DataFrame = analysis["rainday_periods"]
    projection: pd.DataFrame = analysis["projection"]
    fits: dict[str, LinearFit] = analysis["fits"]
    latest_rainfall = rainfall_periods.iloc[-1]
    latest_july = july.iloc[-1]
    latest_raindays = rainday_periods.iloc[-1]
    milestones = {}
    for year in (2050, 2100):
        row = projection.loc[projection["end_year"] == year].iloc[0]
        milestones[str(year)] = {
            "primary_projection_mm": float(row.primary_projection_mm),
            "bootstrap_95_lower_mm": float(row.bootstrap_95_lower_mm),
            "bootstrap_95_upper_mm": float(row.bootstrap_95_upper_mm),
        }
    return {
        "analysis_status": "published-observations-through-july-2026",
        "source_coverage": {
            "rainfall_first_month": rainfall.monthly.iloc[0]["date"].strftime("%Y-%m"),
            "rainfall_last_month": rainfall.monthly.iloc[-1]["date"].strftime("%Y-%m"),
            "raindays_first_month": raindays.monthly.iloc[0]["date"].strftime("%Y-%m"),
            "raindays_last_month": raindays.monthly.iloc[-1]["date"].strftime("%Y-%m"),
        },
        "source_last_updated": {"rainfall": rainfall.source_last_updated, "raindays1mm": raindays.source_last_updated},
        "complete_august_to_july_period_count": len(rainfall_periods),
        "reference_1991_2020": {
            "august_to_july_rainfall_mm": float(analysis["rainfall_reference_mm"]),
            "july_rainfall_mm": float(analysis["july_reference_mm"]),
            "august_to_july_raindays_ge_1mm": float(analysis["rainday_reference_days"]),
        },
        "latest_complete_august_to_july": {
            "period": latest_rainfall.period,
            "rainfall_total_mm": float(latest_rainfall.rainfall_total_mm),
            "percentage_of_1991_2020": float(latest_rainfall.percentage_of_1991_2020),
            "rain_days_ge_1mm": float(latest_raindays.rain_days_ge_1mm),
            "rain_days_percentage_of_1991_2020": float(latest_raindays.rain_days_ge_1mm / analysis["rainday_reference_days"] * 100.0),
        },
        "july_2026": {
            "rainfall_mm": float(latest_july.july_rainfall_mm),
            "percentage_of_1991_2020": float(latest_july.percentage_of_1991_2020),
            "dryness_rank": int(latest_july.dryness_rank),
            "comparison_years": len(july),
        },
        "driest_complete_august_to_july": {
            "period": rainfall_periods.nsmallest(1, "rainfall_total_mm").iloc[0].period,
            "rainfall_total_mm": float(rainfall_periods["rainfall_total_mm"].min()),
        },
        "wettest_complete_august_to_july": {
            "period": rainfall_periods.nlargest(1, "rainfall_total_mm").iloc[0].period,
            "rainfall_total_mm": float(rainfall_periods["rainfall_total_mm"].max()),
        },
        "statistical_projection": {
            "warning": "Illustrative continuation of observed statistical relationships; not a physical climate forecast.",
            "primary_fit": fits["primary"].to_dict(),
            "full_record_fit": fits["full"].to_dict(),
            "theil_sen_fit": fits["robust"].to_dict(),
            "milestones": milestones,
        },
    }
