"""Pure calculation helpers for Project 001."""
from __future__ import annotations
import calendar
from typing import Iterable
import pandas as pd
from source_data import SourceBundle

def with_july_2026(monthly: pd.DataFrame, value: float, status: str) -> pd.DataFrame:
    target = pd.Timestamp("2026-07-01")
    july = pd.DataFrame([{"date": target, "year": 2026, "month": 7, "mean_temperature_c": float(value), "days": 31, "status": status}])
    return pd.concat([monthly[monthly["date"] != target], july], ignore_index=True).sort_values("date").reset_index(drop=True)

def weighted_mean(frame: pd.DataFrame) -> float:
    if frame.empty:
        raise ValueError("Cannot calculate an empty mean")
    return float((frame["mean_temperature_c"] * frame["days"]).sum() / frame["days"].sum())

def august_to_july_series(monthly: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for end_year in range(int(monthly["year"].min()) + 1, int(monthly["year"].max()) + 1):
        start, end = pd.Timestamp(end_year - 1, 8, 1), pd.Timestamp(end_year, 7, 1)
        window = monthly[monthly["date"].between(start, end)]
        if len(window) == 12:
            rows.append({"period": f"{end_year - 1}-08 to {end_year}-07", "start_date": start.date().isoformat(),
                "end_date": pd.Timestamp(end_year, 7, 31).date().isoformat(), "end_year": end_year,
                "mean_temperature_c": weighted_mean(window), "days": int(window["days"].sum()),
                "status": "provisional-scenario" if (window["status"] != "published_monthly_series").any() else "published-inputs"})
    result = pd.DataFrame(rows)
    result["rank_warmest"] = result["mean_temperature_c"].rank(method="min", ascending=False).astype(int)
    return result.sort_values("end_year").reset_index(drop=True)

def all_rolling_12_month_series(monthly: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for end in range(11, len(monthly)):
        window = monthly.iloc[end - 11:end + 1]
        expected = pd.date_range(window.iloc[0]["date"], window.iloc[-1]["date"], freq="MS")
        if expected.equals(pd.DatetimeIndex(window["date"])):
            rows.append({"start_month": window.iloc[0]["date"].date().isoformat(), "end_month": window.iloc[-1]["date"].date().isoformat(),
                "mean_temperature_c": weighted_mean(window), "days": int(window["days"].sum()),
                "status": "provisional-scenario" if (window["status"] != "published_monthly_series").any() else "published-inputs"})
    result = pd.DataFrame(rows)
    result["rank_warmest"] = result["mean_temperature_c"].rank(method="min", ascending=False).astype(int)
    return result

def reference_value_for_target_sequence(monthly: pd.DataFrame, start_year: int, end_year: int) -> float:
    reference = monthly[monthly["year"].between(start_year, end_year)]
    expected = (end_year - start_year + 1) * 12
    if len(reference) != expected:
        raise ValueError(f"Reference period incomplete: expected {expected}, found {len(reference)}")
    normals = reference.groupby("month")["mean_temperature_c"].mean()
    target = pd.date_range("2025-08-01", "2026-07-01", freq="MS")
    weights = [(date.month, calendar.monthrange(date.year, date.month)[1]) for date in target]
    return sum(float(normals.loc[month]) * days for month, days in weights) / sum(days for _, days in weights)

def annual_reconciliation(bundle: SourceBundle) -> pd.DataFrame:
    rows = []
    for record in bundle.annual.itertuples(index=False):
        frame = bundle.monthly[bundle.monthly["year"] == int(record.year)]
        if len(frame) == 12:
            derived = weighted_mean(frame); difference = derived - float(record.official_annual_mean_c)
            rows.append({"year": int(record.year), "derived_from_rounded_months_c": derived,
                "official_annual_mean_c": float(record.official_annual_mean_c), "difference_c": difference,
                "absolute_difference_c": abs(difference)})
    return pd.DataFrame(rows, columns=["year", "derived_from_rounded_months_c", "official_annual_mean_c", "difference_c", "absolute_difference_c"])

def required_july_to_break_record(monthly: pd.DataFrame, previous: float) -> float:
    known = monthly[monthly["date"].between("2025-08-01", "2026-06-01")]
    if len(known) != 11:
        raise ValueError("Expected eleven published months")
    return (previous * 365 - float((known["mean_temperature_c"] * known["days"]).sum())) / 31

def sensitivity_table(monthly: pd.DataFrame, values: Iterable[float]) -> pd.DataFrame:
    rows = []
    for value in values:
        current = august_to_july_series(with_july_2026(monthly, value, "provisional_scenario")).iloc[-1]
        rows.append({"july_2026_scenario_c": value, "aug_2025_to_jul_2026_mean_c": current["mean_temperature_c"],
            "rank_among_aug_to_jul_periods": int(current["rank_warmest"])})
    return pd.DataFrame(rows)
