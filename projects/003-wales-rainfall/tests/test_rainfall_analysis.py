from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))
SPEC = importlib.util.spec_from_file_location("rainfall_analysis", PROJECT_DIR / "analysis.py")
assert SPEC and SPEC.loader
analysis = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = analysis
SPEC.loader.exec_module(analysis)


def _official_style_source(path: Path) -> None:
    header = "year    jan    feb    mar    apr    may    jun    jul    aug    sep    oct    nov    dec     win     spr     sum     aut     ann"

    def row(values: dict[str, str]) -> str:
        chars = [" "] * 129
        for name, start, end in analysis.FIELD_SPECS:
            value = values.get(name, "")
            if len(value) > end - start:
                raise ValueError(f"Fixture value too wide for {name}")
            chars[start:end] = list(value.rjust(end - start))
        return "".join(chars).rstrip()

    lines = [
        "Areal values from HadUK-Grid 1km gridded climate data from land surface network",
        "Source: Met Office National Climate Information Centre",
        "Monthly, seasonal and annual total precipitation amount for Wales",
        "Areal series, starting in 1836",
        "Last updated 01-Jul-2026 11:33",
        header,
        row({"year": "1836", **{month: "10.0" for month in analysis.MONTH_COLUMNS}, "win": "---", "ann": "120.0"}),
        row({"year": "1837", **{month: "20.0" for month in analysis.MONTH_COLUMNS}, "ann": "240.0"}),
        row({"year": "1838", "jan": "30.0", "feb": "40.0", "win": "90.0"}),
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_fixed_width_parser_preserves_missing_months(tmp_path: Path) -> None:
    source = tmp_path / "rainfall.txt"
    _official_style_source(source)
    bundle = analysis.load_source(source)
    assert len(bundle.monthly) == 26
    assert bundle.monthly.iloc[-1]["date"] == pd.Timestamp("1838-02-01")
    assert pd.isna(bundle.annual.loc[bundle.annual["year"] == 1838, "jul"]).all()
    assert bundle.annual.loc[bundle.annual["year"] == 1838, "win"].iloc[0] == 90.0
    reconciliation = analysis.annual_reconciliation(bundle)
    assert reconciliation["difference_mm"].abs().max() == 0


def test_august_to_july_sums_only_complete_calendar_window() -> None:
    dates = pd.date_range("2000-01-01", "2002-12-01", freq="MS")
    monthly = pd.DataFrame({
        "date": dates,
        "year": dates.year,
        "month": dates.month,
        "month_name": [analysis.MONTH_COLUMNS[month - 1] for month in dates.month],
        "rainfall_mm": np.arange(1, len(dates) + 1, dtype=float),
    })
    periods = analysis.august_to_july_series(monthly)
    first = periods.iloc[0]
    expected = monthly[
        (monthly["date"] >= "2000-08-01") & (monthly["date"] <= "2001-07-01")
    ]["rainfall_mm"].sum()
    assert first.period == "2000-08 to 2001-07"
    assert first.rainfall_total_mm == expected


def test_reference_is_sum_of_monthly_1991_2020_normals() -> None:
    dates = pd.date_range("1991-01-01", "2020-12-01", freq="MS")
    monthly = pd.DataFrame({
        "date": dates,
        "year": dates.year,
        "month": dates.month,
        "month_name": [analysis.MONTH_COLUMNS[month - 1] for month in dates.month],
        "rainfall_mm": dates.month.astype(float),
    })
    assert analysis.reference_total(monthly, 1991, 2020, list(range(1, 13))) == 78.0
    assert analysis.reference_total(
        monthly,
        1991,
        2020,
        [8, 9, 10, 11, 12, 1, 2, 3, 4, 5, 6],
    ) == 71.0


def test_linear_fit_recovers_known_trend() -> None:
    years = np.arange(1970, 2026)
    values = 1300.0 + 2.5 * (years - 2000)
    fit = analysis.fit_linear(years, values)
    assert abs(fit.intercept_at_2000_mm - 1300.0) < 1e-10
    assert abs(fit.slope_mm_per_decade - 25.0) < 1e-10
    assert abs(fit.r_squared - 1.0) < 1e-12


def test_history_figure_has_exact_dimensions(tmp_path: Path) -> None:
    years = np.arange(1980, 2026)
    series = pd.DataFrame({
        "period": [f"{year-1}-08 to {year}-07" for year in years],
        "end_year": years,
        "rainfall_total_mm": 1300 + np.sin(years) * 100,
        "reference_1991_2020_mm": 1300.0,
    })
    partial = pd.Series({"rainfall_total_mm": 1200.0})
    output = tmp_path / "history"
    analysis.make_history_figure(series, partial, 1200.0, output, "01-Jul-2026 11:33")
    with Image.open(output.with_suffix(".png")) as image:
        assert image.size == (1600, 900)
    assert "July is not yet published" in output.with_suffix(".svg").read_text(encoding="utf-8")
