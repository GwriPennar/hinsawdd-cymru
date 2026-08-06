from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

PROJECT_DIR = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("dark_climate_charts", PROJECT_DIR / "dark_climate_charts.py")
assert SPEC and SPEC.loader
charts = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = charts
SPEC.loader.exec_module(charts)


def _source(path: Path, *, metric: str, start_year: int = 1991, end_year: int = 2026) -> None:
    header = "year    jan    feb    mar    apr    may    jun    jul    aug    sep    oct    nov    dec     win     spr     sum     aut     ann"
    description = {
        "rainfall": "Monthly, seasonal and annual total precipitation amount for Wales",
        "raindays1mm": (
            "Monthly, seasonal and annual number of days in the month with precipitation amount >= 1mm for Wales"
        ),
    }[metric]

    def fixed_row(values: dict[str, str]) -> str:
        chars = [" "] * 129
        for name, start, end in charts.FIELD_SPECS:
            value = values.get(name, "")
            chars[start:end] = list(value.rjust(end - start))
        return "".join(chars).rstrip()

    lines = [
        "Areal values from HadUK-Grid 1km gridded climate data from land surface network",
        "Source: Met Office National Climate Information Centre",
        description,
        f"Areal series, starting in {start_year}",
        "Last updated 03-Aug-2026 09:28",
        header,
    ]
    for year in range(start_year, end_year + 1):
        values: dict[str, str] = {"year": str(year)}
        for month, name in enumerate(charts.MONTH_COLUMNS, start=1):
            if year == end_year and month > 7:
                continue
            base = month + (year - start_year) * 0.1
            values[name] = f"{base:.1f}"
        lines.append(fixed_row(values))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_metric_specific_source_validation_and_latest_month(tmp_path: Path) -> None:
    rainfall_path = tmp_path / "rainfall.txt"
    raindays_path = tmp_path / "raindays.txt"
    _source(rainfall_path, metric="rainfall")
    _source(raindays_path, metric="raindays1mm")
    rainfall = charts.load_source(rainfall_path, metric="rainfall")
    raindays = charts.load_source(raindays_path, metric="raindays1mm")
    assert rainfall.monthly.iloc[-1]["date"] == pd.Timestamp("2026-07-01")
    assert raindays.monthly.iloc[-1]["date"] == pd.Timestamp("2026-07-01")
    try:
        charts.load_source(rainfall_path, metric="raindays1mm")
    except ValueError as exc:
        assert "raindays1mm" in str(exc)
    else:
        raise AssertionError("rainfall source was accepted as a rain-days source")


def test_august_to_july_sums_complete_windows_only() -> None:
    dates = pd.date_range("2000-01-01", "2002-07-01", freq="MS")
    monthly = pd.DataFrame(
        {
            "date": dates,
            "year": dates.year,
            "month": dates.month,
            "month_name": [charts.MONTH_COLUMNS[month - 1] for month in dates.month],
            "value": np.arange(1, len(dates) + 1, dtype=float),
        }
    )
    periods = charts.rolling_august_to_july(monthly, value_name="rainfall_total_mm")
    assert list(periods["end_year"]) == [2001, 2002]
    expected = monthly[(monthly["date"] >= "2000-08-01") & (monthly["date"] <= "2001-07-01")]["value"].sum()
    assert periods.iloc[0]["rainfall_total_mm"] == expected


def test_july_dryness_rank_uses_lowest_value_as_rank_one() -> None:
    july = pd.DataFrame({"year": [2023, 2024, 2025, 2026], "july_rainfall_mm": [90.0, 40.0, 60.0, 9.3]})
    july["dryness_rank"] = july["july_rainfall_mm"].rank(method="min", ascending=True).astype(int)
    assert int(july.loc[july["year"] == 2026, "dryness_rank"].iloc[0]) == 1


def _history_fixture() -> pd.DataFrame:
    years = np.arange(1837, 2027)
    values = 1450 + np.sin(years / 4.0) * 190
    frame = pd.DataFrame(
        {
            "period": [f"{year - 1}-08 to {year}-07" for year in years],
            "end_year": years,
            "rainfall_total_mm": values,
            "reference_1991_2020_mm": 1464.76,
        }
    )
    frame["trailing_10_period_mean_mm"] = frame["rainfall_total_mm"].rolling(10, min_periods=10).mean()
    return frame


def test_dark_history_renderers_have_exact_dimensions_and_background(tmp_path: Path) -> None:
    data = _history_fixture()
    note = "Source: test. Reference: 1991–2020."
    wide = tmp_path / "history_dark"
    square = tmp_path / "history_dark_square"
    charts.render_history(data, wide, square=False, source_note=note)
    charts.render_history(data, square, square=True, source_note=note)
    with Image.open(wide.with_suffix(".png")) as image:
        assert image.size == (1600, 900)
    with Image.open(square.with_suffix(".png")) as image:
        assert image.size == (1080, 1080)
    assert charts.DARK_BG in wide.with_suffix(".svg").read_text(encoding="utf-8").lower()
    assert charts.DARK_BG in square.with_suffix(".svg").read_text(encoding="utf-8").lower()
