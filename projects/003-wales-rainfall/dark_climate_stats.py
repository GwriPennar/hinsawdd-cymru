"""Period construction and transparent statistical fits."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from dark_climate_constants import LinearFit

def rolling_august_to_july(monthly: pd.DataFrame, *, value_name: str) -> pd.DataFrame:
    data = monthly.set_index("date")["value"].sort_index()
    rows: list[dict[str, object]] = []
    for end_date in data.index[data.index.month == 7]:
        start_date = end_date - pd.DateOffset(months=11)
        expected = pd.date_range(start_date, end_date, freq="MS")
        if not expected.isin(data.index).all():
            continue
        rows.append(
            {
                "period": f"{start_date.year:04d}-{start_date.month:02d} to {end_date.year:04d}-{end_date.month:02d}",
                "start_year": int(start_date.year),
                "end_year": int(end_date.year),
                value_name: float(data.loc[expected].sum()),
            }
        )
    return pd.DataFrame(rows)


def monthly_reference(monthly: pd.DataFrame, start_year: int = 1991, end_year: int = 2020) -> pd.Series:
    reference = monthly[(monthly["year"] >= start_year) & (monthly["year"] <= end_year)]
    means = reference.groupby("month")["value"].mean()
    if len(means) != 12:
        raise ValueError("Reference period lacks calendar months")
    return means


def fit_linear(years: pd.Series | np.ndarray, values: pd.Series | np.ndarray) -> LinearFit:
    x_years = np.asarray(years, dtype=float)
    y = np.asarray(values, dtype=float)
    if len(x_years) < 3 or len(x_years) != len(y) or not np.isfinite(y).all():
        raise ValueError("Linear fit requires at least three finite paired observations")
    x = x_years - 2000.0
    x_mean = float(x.mean())
    y_mean = float(y.mean())
    denominator = float(np.sum((x - x_mean) ** 2))
    slope = float(np.sum((x - x_mean) * (y - y_mean)) / denominator)
    intercept = y_mean - slope * x_mean
    residuals = y - (intercept + slope * x)
    ss_res = float(np.sum(residuals**2))
    ss_tot = float(np.sum((y - y_mean) ** 2))
    return LinearFit(
        intercept,
        slope,
        1.0 - ss_res / ss_tot if ss_tot else 0.0,
        math.sqrt(ss_res / (len(y) - 2)),
        len(y),
        int(x_years.min()),
        int(x_years.max()),
    )


def fit_theil_sen(years: pd.Series | np.ndarray, values: pd.Series | np.ndarray) -> LinearFit:
    x_years = np.asarray(years, dtype=float)
    y = np.asarray(values, dtype=float)
    slopes = [
        (y[j] - y[i]) / (x_years[j] - x_years[i])
        for i in range(len(y) - 1)
        for j in range(i + 1, len(y))
        if x_years[j] != x_years[i]
    ]
    slope = float(np.median(slopes))
    intercept = float(np.median(y - slope * (x_years - 2000.0)))
    residuals = y - (intercept + slope * (x_years - 2000.0))
    ss_res = float(np.sum(residuals**2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    return LinearFit(
        intercept,
        slope,
        1.0 - ss_res / ss_tot if ss_tot else 0.0,
        math.sqrt(ss_res / max(len(y) - 2, 1)),
        len(y),
        int(x_years.min()),
        int(x_years.max()),
    )


def bootstrap_projection(
    training: pd.DataFrame,
    years: np.ndarray,
    *,
    replicates: int = 2000,
    block_length: int = 5,
    seed: int = 20260806,
) -> tuple[np.ndarray, np.ndarray]:
    x_years = training["end_year"].to_numpy(dtype=float)
    values = training["rainfall_total_mm"].to_numpy(dtype=float)
    base = fit_linear(x_years, values)
    fitted = base.predict(x_years)
    residuals = values - fitted
    count = len(residuals)
    rng = np.random.default_rng(seed)
    predictions = np.empty((replicates, len(years)), dtype=float)
    for replicate in range(replicates):
        sample: list[float] = []
        while len(sample) < count:
            start = int(rng.integers(0, count))
            sample.extend(float(residuals[(start + offset) % count]) for offset in range(block_length))
        predictions[replicate] = fit_linear(x_years, fitted + np.asarray(sample[:count])).predict(years)
    return np.quantile(predictions, 0.025, axis=0), np.quantile(predictions, 0.975, axis=0)
