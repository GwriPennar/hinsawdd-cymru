"""Project 003: Wales rainfall history, trends and statistical baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from fetch_source import SERIES_URL

PROJECT_DIR = Path(__file__).resolve().parent
RAW_DIR = PROJECT_DIR / "data/raw"
DERIVED_DIR = PROJECT_DIR / "data/derived"
FIGURES_DIR = PROJECT_DIR / "figures"
README_PATH = PROJECT_DIR / "README.md"
RESULT_START = "<!-- BEGIN GENERATED RESULT -->"
RESULT_END = "<!-- END GENERATED RESULT -->"
MONTH_COLUMNS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
MONTH_NUMBERS = {name: index for index, name in enumerate(MONTH_COLUMNS, start=1)}
SEASON_COLUMNS = ["win", "spr", "sum", "aut"]


@dataclass(frozen=True)
class SourceBundle:
    path: Path
    annual: pd.DataFrame
    monthly: pd.DataFrame
    source_last_updated: str
    sha256: str


@dataclass(frozen=True)
class LinearFit:
    intercept_at_2000_mm: float
    slope_mm_per_year: float
    r_squared: float
    residual_standard_error_mm: float
    observation_count: int
    first_end_year: int
    last_end_year: int

    @property
    def slope_mm_per_decade(self) -> float:
        return self.slope_mm_per_year * 10.0

    def predict(self, years: np.ndarray | pd.Series | list[int]) -> np.ndarray:
        values = np.asarray(years, dtype=float)
        return self.intercept_at_2000_mm + self.slope_mm_per_year * (values - 2000.0)

    def to_dict(self) -> dict[str, float | int]:
        result = asdict(self)
        result["slope_mm_per_decade"] = self.slope_mm_per_decade
        return result


@dataclass(frozen=True)
class AnalysisConfig:
    reference_start_year: int = 1991
    reference_end_year: int = 2020
    modern_fit_start_end_year: int = 1970
    projection_end_year: int = 2100
    bootstrap_replicates: int = 2000
    bootstrap_block_length: int = 5
    random_seed: int = 20260803
    backtest_horizon_years: int = 10
    backtest_cutoffs: tuple[int, ...] = (1990, 2000, 2010, 2015)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def discover_source() -> Path:
    candidates = sorted(RAW_DIR.glob("metoffice-wales-rainfall-source-*.txt"))
    if not candidates:
        candidates = sorted(RAW_DIR.glob("metoffice-wales-rainfall-retrieved-*.txt"))
    if not candidates:
        raise FileNotFoundError("No retained or retrieved Met Office Wales rainfall source was found")
    return candidates[-1]


def _fixed_width_rows(text: str) -> tuple[list[str], list[dict[str, str]]]:
    lines = text.splitlines()
    header_index = next((i for i, line in enumerate(lines) if line.lstrip().startswith("year")), None)
    if header_index is None:
        raise ValueError("Could not locate the official source table header")
    matches = list(re.finditer(r"\S+", lines[header_index]))
    columns = [match.group(0).lower() for match in matches]
    starts = [match.start() for match in matches]
    if columns != ["year", *MONTH_COLUMNS, *SEASON_COLUMNS, "ann"]:
        raise ValueError(f"Unexpected rainfall columns: {columns}")
    rows: list[dict[str, str]] = []
    for line in lines[header_index + 1 :]:
        if not re.match(r"^\s*\d{4}\b", line):
            continue
        row: dict[str, str] = {}
        for index, column in enumerate(columns):
            end = starts[index + 1] if index + 1 < len(starts) else None
            row[column] = line[starts[index] : end].strip()
        rows.append(row)
    if not rows:
        raise ValueError("No rainfall rows were parsed")
    return columns, rows


def load_source(path: Path) -> SourceBundle:
    text = path.read_text(encoding="utf-8")
    required = (
        "Areal values from HadUK-Grid 1km gridded climate data from land surface network",
        "Monthly, seasonal and annual total precipitation amount for Wales",
        "Areal series, starting in 1836",
    )
    if any(item not in text for item in required):
        raise ValueError("The supplied file is not the expected Met Office Wales rainfall series")
    updated_match = re.search(r"^Last updated\s+(.+)$", text, re.MULTILINE)
    if updated_match is None:
        raise ValueError("Missing source Last updated field")

    columns, rows = _fixed_width_rows(text)
    parsed: list[dict[str, float | int | None]] = []
    for row in rows:
        item: dict[str, float | int | None] = {"year": int(row["year"])}
        for column in columns[1:]:
            raw = row[column]
            item[column] = None if raw in {"", "---"} else float(raw)
        parsed.append(item)

    annual = pd.DataFrame(parsed).sort_values("year").reset_index(drop=True)
    if int(annual.iloc[0]["year"]) != 1836:
        raise ValueError("The rainfall series does not begin in 1836")

    monthly_rows: list[dict[str, object]] = []
    for row in parsed:
        year = int(row["year"])
        for month_name in MONTH_COLUMNS:
            value = row[month_name]
            if value is None:
                continue
            rainfall = float(value)
            if rainfall < 0:
                raise ValueError("Rainfall totals cannot be negative")
            month = MONTH_NUMBERS[month_name]
            monthly_rows.append({
                "date": pd.Timestamp(year=year, month=month, day=1),
                "year": year,
                "month": month,
                "month_name": month_name,
                "rainfall_mm": rainfall,
            })
    monthly = pd.DataFrame(monthly_rows).sort_values("date").reset_index(drop=True)
    expected = pd.date_range(monthly["date"].min(), monthly["date"].max(), freq="MS")
    if not monthly["date"].equals(pd.Series(expected, name="date")):
        raise ValueError("Published monthly rainfall coverage is not continuous")
    return SourceBundle(path, annual, monthly, updated_match.group(1).strip(), sha256(path))


def annual_reconciliation(bundle: SourceBundle) -> pd.DataFrame:
    reconstructed = bundle.monthly.groupby("year", as_index=False).agg(
        monthly_count=("rainfall_mm", "count"),
        reconstructed_annual_mm=("rainfall_mm", "sum"),
    )
    official = bundle.annual[["year", "ann"]].rename(columns={"ann": "official_annual_mm"})
    result = reconstructed.merge(official, on="year", how="left")
    result = result[(result["monthly_count"] == 12) & result["official_annual_mm"].notna()].copy()
    result["difference_mm"] = result["reconstructed_annual_mm"] - result["official_annual_mm"]
    return result.reset_index(drop=True)


def _rolling_periods(monthly: pd.DataFrame, months: int, ending_month: int) -> pd.DataFrame:
    data = monthly.set_index("date")["rainfall_mm"].sort_index()
    totals = data.rolling(months, min_periods=months).sum()
    selected = totals[(totals.index.month == ending_month) & totals.notna()]
    rows: list[dict[str, object]] = []
    for end_date, total in selected.items():
        start_date = end_date - pd.DateOffset(months=months - 1)
        expected = pd.date_range(start_date, end_date, freq="MS")
        if len(expected) != months or not expected.isin(data.index).all():
            continue
        rows.append({
            "period": f"{start_date.year:04d}-{start_date.month:02d} to {end_date.year:04d}-{end_date.month:02d}",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "start_year": int(start_date.year),
            "end_year": int(end_date.year),
            "months": months,
            "rainfall_total_mm": float(total),
            "status": "published-inputs",
        })
    return pd.DataFrame(rows)


def august_to_july_series(monthly: pd.DataFrame) -> pd.DataFrame:
    return _rolling_periods(monthly, 12, 7)


def august_to_june_series(monthly: pd.DataFrame) -> pd.DataFrame:
    return _rolling_periods(monthly, 11, 6)


def reference_total(monthly: pd.DataFrame, start_year: int, end_year: int, months: list[int]) -> float:
    subset = monthly[(monthly["year"] >= start_year) & (monthly["year"] <= end_year)]
    means = subset.groupby("month")["rainfall_mm"].mean()
    missing = [month for month in months if month not in means.index]
    if missing:
        raise ValueError(f"Reference period lacks months: {missing}")
    return float(sum(float(means.loc[month]) for month in months))


def attach_reference(series: pd.DataFrame, reference_mm: float) -> pd.DataFrame:
    result = series.copy()
    result["reference_1991_2020_mm"] = reference_mm
    result["anomaly_mm"] = result["rainfall_total_mm"] - reference_mm
    result["percentage_of_1991_2020"] = result["rainfall_total_mm"] / reference_mm * 100.0
    return result


def fit_linear(years: pd.Series | np.ndarray, values: pd.Series | np.ndarray) -> LinearFit:
    x_years = np.asarray(years, dtype=float)
    y = np.asarray(values, dtype=float)
    if len(x_years) < 3 or len(x_years) != len(y) or not np.isfinite(y).all():
        raise ValueError("A linear fit requires at least three finite paired observations")
    x = x_years - 2000.0
    x_mean, y_mean = float(x.mean()), float(y.mean())
    denominator = float(np.sum((x - x_mean) ** 2))
    if denominator == 0:
        raise ValueError("Cannot fit a line to identical years")
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


def bootstrap_projection(training: pd.DataFrame, years: np.ndarray, config: AnalysisConfig) -> tuple[np.ndarray, np.ndarray]:
    x_years = training["end_year"].to_numpy(dtype=float)
    values = training["rainfall_total_mm"].to_numpy(dtype=float)
    base = fit_linear(x_years, values)
    fitted = base.predict(x_years)
    residuals = values - fitted
    n = len(residuals)
    rng = np.random.default_rng(config.random_seed)
    predictions = np.empty((config.bootstrap_replicates, len(years)), dtype=float)
    for replicate in range(config.bootstrap_replicates):
        sample: list[float] = []
        while len(sample) < n:
            start = int(rng.integers(0, n))
            sample.extend(float(residuals[(start + offset) % n]) for offset in range(config.bootstrap_block_length))
        boot_fit = fit_linear(x_years, fitted + np.asarray(sample[:n]))
        predictions[replicate] = boot_fit.predict(years)
    return np.quantile(predictions, 0.025, axis=0), np.quantile(predictions, 0.975, axis=0)


def run_backtests(series: pd.DataFrame, config: AnalysisConfig) -> pd.DataFrame:
    rows: list[dict[str, float | int]] = []
    for cutoff in config.backtest_cutoffs:
        training = series[(series["end_year"] >= config.modern_fit_start_end_year) & (series["end_year"] <= cutoff)]
        actual = series[(series["end_year"] > cutoff) & (series["end_year"] <= cutoff + config.backtest_horizon_years)]
        if len(training) < 10 or len(actual) != config.backtest_horizon_years:
            continue
        predictions = fit_linear(training["end_year"], training["rainfall_total_mm"]).predict(actual["end_year"])
        errors = predictions - actual["rainfall_total_mm"].to_numpy(dtype=float)
        rows.append({
            "cutoff_end_year": cutoff,
            "training_observations": len(training),
            "test_observations": len(actual),
            "annual_mae_mm": float(np.mean(np.abs(errors))),
            "annual_rmse_mm": float(np.sqrt(np.mean(errors**2))),
            "predicted_ten_year_mean_mm": float(np.mean(predictions)),
            "observed_ten_year_mean_mm": float(actual["rainfall_total_mm"].mean()),
            "ten_year_mean_error_mm": float(np.mean(predictions) - actual["rainfall_total_mm"].mean()),
        })
    return pd.DataFrame(rows)


def seasonal_trends(annual: pd.DataFrame, reference: float, modern_start: int) -> pd.DataFrame:
    labels = {"win": "winter", "spr": "spring", "sum": "summer", "aut": "autumn"}
    rows: list[dict[str, object]] = []
    for column in SEASON_COLUMNS:
        subset = annual[["year", column]].dropna().rename(columns={column: "rainfall_mm"})
        full = fit_linear(subset["year"], subset["rainfall_mm"])
        modern_subset = subset[subset["year"] >= modern_start]
        modern = fit_linear(modern_subset["year"], modern_subset["rainfall_mm"])
        rows.append({
            "season": labels[column],
            "full_record_slope_mm_per_decade": full.slope_mm_per_decade,
            "modern_slope_mm_per_decade": modern.slope_mm_per_decade,
            "reference_1991_2020_annual_mm": reference,
        })
    return pd.DataFrame(rows)


def make_history_figure(series: pd.DataFrame, partial: pd.Series, partial_reference_mm: float, output: Path, source_last_updated: str) -> None:
    data = series.copy()
    data["trailing_10_period_mean_mm"] = data["rainfall_total_mm"].rolling(10, min_periods=10).mean()
    reference = float(data["reference_1991_2020_mm"].iloc[0])
    wettest, driest, latest = data.nlargest(1, "rainfall_total_mm").iloc[0], data.nsmallest(1, "rainfall_total_mm").iloc[0], data.iloc[-1]
    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none"})
    fig, ax = plt.subplots(figsize=(16, 9), dpi=100)
    ax.plot(data["end_year"], data["rainfall_total_mm"], linewidth=1.15, alpha=0.68, label="Complete August-to-July totals")
    ax.plot(data["end_year"], data["trailing_10_period_mean_mm"], linewidth=3.0, label="Trailing 10-period mean")
    ax.axhline(reference, linestyle="--", linewidth=2.0, label="Derived 1991–2020 reference")
    for row, label, offset in ((wettest, "Wettest", (12, 16)), (driest, "Driest", (12, -32)), (latest, "Latest complete", (-12, 16))):
        ax.scatter([row.end_year], [row.rainfall_total_mm], s=70, zorder=6)
        ax.annotate(
            f"{label}\n{row.period}: {row.rainfall_total_mm:.1f} mm",
            (row.end_year, row.rainfall_total_mm),
            xytext=offset,
            textcoords="offset points",
            ha="right" if offset[0] < 0 else "left",
            fontsize=9,
        )
    partial_percent = float(partial["rainfall_total_mm"]) / partial_reference_mm * 100.0
    ax.text(
        0.015,
        0.965,
        f"Current incomplete period, Aug 2025–Jun 2026: {partial['rainfall_total_mm']:.1f} mm\n{partial_percent:.1f}% of the derived 1991–2020 August–June reference; July is not yet published",
        transform=ax.transAxes,
        va="top",
        fontsize=11,
        bbox={"boxstyle": "round,pad=0.45", "facecolor": "white", "edgecolor": "0.55", "alpha": 0.95},
    )
    ax.set_title("Wales August-to-July rainfall since records began", fontsize=24, fontweight="bold", pad=18)
    ax.set_xlabel("Period end year")
    ax.set_ylabel("Total precipitation (mm)")
    ax.set_xlim(int(data["end_year"].min()) - 1, int(data["end_year"].max()) + 2)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=True, loc="upper right", fontsize=10)
    fig.text(0.01, 0.012, f"Data source: Met Office National Climate Information Centre, Wales HadUK-Grid 1 km areal rainfall series. Source last updated {source_last_updated}. Monthly rainfall totals are summed; no temperature-style day weighting is applied.", fontsize=8.5)
    fig.tight_layout(rect=(0, 0.045, 1, 1))
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output.with_suffix(".png"), dpi=100, facecolor="white")
    fig.savefig(output.with_suffix(".svg"), facecolor="white")
    plt.close(fig)


def make_projection_figure(series: pd.DataFrame, primary: LinearFit, full: LinearFit, robust: LinearFit, projection: pd.DataFrame, output: Path) -> None:
    data = series.copy()
    data["trailing_10_period_mean_mm"] = data["rainfall_total_mm"].rolling(10, min_periods=10).mean()
    reference = float(data["reference_1991_2020_mm"].iloc[0])
    future = projection[projection["end_year"] >= primary.last_end_year]
    years = future["end_year"].to_numpy(dtype=float)
    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none"})
    fig, ax = plt.subplots(figsize=(16, 9), dpi=100)
    ax.plot(data["end_year"], data["rainfall_total_mm"], linewidth=1.0, alpha=0.35, label="Published complete periods")
    ax.plot(data["end_year"], data["trailing_10_period_mean_mm"], linewidth=2.6, label="Trailing 10-period mean")
    fit_years = np.arange(primary.first_end_year, primary.last_end_year + 1)
    ax.plot(fit_years, primary.predict(fit_years), linewidth=2.8, label="Modern OLS fit, 1970–2025")
    ax.fill_between(years, future["bootstrap_95_lower_mm"], future["bootstrap_95_upper_mm"], alpha=0.22, label="95% trend-fit bootstrap range")
    ax.plot(years, future["primary_projection_mm"], linewidth=3.0, linestyle="--", label="Illustrative continuation")
    ax.plot(years, full.predict(years), linewidth=1.8, linestyle=":", label="Full-record OLS sensitivity")
    ax.plot(years, robust.predict(years), linewidth=1.8, linestyle="-.", label="Modern Theil–Sen sensitivity")
    ax.axhline(reference, linewidth=1.5, linestyle="--", alpha=0.7, label="1991–2020 reference")
    ax.axvline(primary.last_end_year, linewidth=1.2, linestyle=":")
    for milestone in (2050, 2100):
        row = projection.loc[projection["end_year"] == milestone].iloc[0]
        ax.scatter([milestone], [row.primary_projection_mm], s=75, zorder=7)
        ax.annotate(f"{milestone}: {row.primary_projection_mm:.0f} mm", (milestone, row.primary_projection_mm), xytext=(-8, 14), textcoords="offset points", ha="right", fontsize=10)
    ax.set_title("Wales rainfall: illustrative statistical continuation", fontsize=24, fontweight="bold", pad=18)
    ax.text(0.5, 1.01, "Observed August-to-July totals and transparent regression sensitivities — not a physical climate forecast", transform=ax.transAxes, ha="center", fontsize=12)
    ax.set_xlabel("Period end year")
    ax.set_ylabel("Total precipitation (mm)")
    ax.set_xlim(int(data["end_year"].min()), int(projection["end_year"].max()) + 2)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=True, loc="upper left", ncol=2, fontsize=9.5)
    fig.text(0.01, 0.012, "Illustrative continuation of observed statistical relationships only. It does not represent UKCP/UKCI, emissions scenarios, future circulation changes, physical hydrology or year-to-year forecast skill.", fontsize=8.5)
    fig.tight_layout(rect=(0, 0.045, 1, 1))
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output.with_suffix(".png"), dpi=100, facecolor="white")
    fig.savefig(output.with_suffix(".svg"), facecolor="white")
    plt.close(fig)


def _period_table(rows: list[dict[str, object]], heading: str) -> str:
    output = [heading, "", "| Rank | Period | Rainfall | % of 1991–2020 |", "|---:|---|---:|---:|"]
    for item in rows:
        output.append(f"| {item['rank']} | {item['period']} | **{item['rainfall_total_mm']:.1f} mm** | {item['percentage_of_1991_2020']:.1f}% |")
    return "\n".join(output)


def update_readme(summary: dict[str, object]) -> None:
    text = README_PATH.read_text(encoding="utf-8")
    wet = _period_table(summary["wettest_complete_periods"], "### Wettest complete periods")
    dry = _period_table(summary["driest_complete_periods"], "### Driest complete periods")
    latest = summary["latest_complete_period"]
    partial = summary["current_incomplete_period"]
    primary = summary["statistical_projection"]["primary_fit"]
    milestones = summary["statistical_projection"]["milestones"]
    block = f"""{RESULT_START}
## Headline results

| Measure | Result |
|---|---:|
| Official monthly source coverage | **{summary['first_published_month']} to {summary['last_published_month']}** |
| Complete August-to-July periods | **{summary['complete_period_count']}** |
| Derived 1991–2020 August-to-July reference | **{summary['reference_1991_2020_august_july_mm']:.1f} mm** |
| Latest complete period | **{latest['period']}** |
| Latest complete rainfall | **{latest['rainfall_total_mm']:.1f} mm**, {latest['percentage_of_1991_2020']:.1f}% of reference |
| Current incomplete period | **{partial['period']}**, {partial['months']} published months |
| Current incomplete rainfall | **{partial['rainfall_total_mm']:.1f} mm**, {partial['percentage_of_partial_reference']:.1f}% of the like-for-like August–June reference |
| Current partial rank among historical August–June periods | **{partial['wetness_rank']} of {partial['comparison_period_count']}** |
| Full-record trend | **{summary['trends']['full_record']['slope_mm_per_decade']:+.1f} mm per decade** |
| Modern trend, 1970 onward | **{primary['slope_mm_per_decade']:+.1f} mm per decade** |
| Illustrative 2050 continuation | **{milestones['2050']['primary_projection_mm']:.0f} mm** |
| Illustrative 2100 continuation | **{milestones['2100']['primary_projection_mm']:.0f} mm** |

The official Wales series currently stops at June 2026. The August 2025–July 2026 total is therefore **not complete and is not ranked against complete twelve-month periods**. It is compared only with historical August-to-June totals until July is published.

The projection is deliberately secondary. It is a transparent statistical baseline, not a physical rainfall forecast or an official Met Office, UKCP or UKCI projection.

{wet}

{dry}
{RESULT_END}"""
    pattern = re.compile(re.escape(RESULT_START) + r".*?" + re.escape(RESULT_END), re.DOTALL)
    if not pattern.search(text):
        raise ValueError("README generated-result markers missing")
    README_PATH.write_text(pattern.sub(block, text), encoding="utf-8")


def run(source_path: Path | None = None, *, config: AnalysisConfig = AnalysisConfig(), update_project_readme: bool = True) -> dict[str, object]:
    source_path = source_path or discover_source()
    bundle = load_source(source_path)
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    complete_reference = reference_total(bundle.monthly, config.reference_start_year, config.reference_end_year, list(range(1, 13)))
    partial_reference = reference_total(bundle.monthly, config.reference_start_year, config.reference_end_year, [8, 9, 10, 11, 12, 1, 2, 3, 4, 5, 6])
    complete = attach_reference(august_to_july_series(bundle.monthly), complete_reference)
    partials = august_to_june_series(bundle.monthly)
    partials["reference_1991_2020_august_june_mm"] = partial_reference
    partials["percentage_of_partial_reference"] = partials["rainfall_total_mm"] / partial_reference * 100.0
    partials["wetness_rank"] = partials["rainfall_total_mm"].rank(method="min", ascending=False).astype(int)
    latest_complete, current_partial = complete.iloc[-1], partials.iloc[-1]
    if current_partial["end_year"] != int(bundle.monthly.iloc[-1]["year"]):
        raise ValueError("Current partial-period construction did not reach the latest published month")

    modern = complete[complete["end_year"] >= config.modern_fit_start_end_year].copy()
    primary = fit_linear(modern["end_year"], modern["rainfall_total_mm"])
    full = fit_linear(complete["end_year"], complete["rainfall_total_mm"])
    robust = fit_theil_sen(modern["end_year"], modern["rainfall_total_mm"])
    projection_years = np.arange(primary.last_end_year, config.projection_end_year + 1)
    lower, upper = bootstrap_projection(modern, projection_years, config)
    projection = pd.DataFrame({
        "end_year": projection_years.astype(int),
        "primary_projection_mm": primary.predict(projection_years),
        "bootstrap_95_lower_mm": lower,
        "bootstrap_95_upper_mm": upper,
        "full_record_sensitivity_mm": full.predict(projection_years),
        "theil_sen_sensitivity_mm": robust.predict(projection_years),
    })
    backtests = run_backtests(complete, config)
    reconciliation = annual_reconciliation(bundle)
    season_trends = seasonal_trends(bundle.annual, complete_reference, config.modern_fit_start_end_year)

    def ranked_rows(frame: pd.DataFrame) -> list[dict[str, object]]:
        return [
            {
                "rank": index,
                "period": row.period,
                "rainfall_total_mm": float(row.rainfall_total_mm),
                "percentage_of_1991_2020": float(row.percentage_of_1991_2020),
            }
            for index, row in enumerate(frame.itertuples(), start=1)
        ]

    wet_rows = ranked_rows(complete.nlargest(10, "rainfall_total_mm"))
    dry_rows = ranked_rows(complete.nsmallest(10, "rainfall_total_mm"))
    milestones: dict[str, dict[str, float]] = {}
    for year in (2050, 2100):
        row = projection.loc[projection["end_year"] == year].iloc[0]
        milestones[str(year)] = {
            "primary_projection_mm": float(row.primary_projection_mm),
            "bootstrap_95_lower_mm": float(row.bootstrap_95_lower_mm),
            "bootstrap_95_upper_mm": float(row.bootstrap_95_upper_mm),
            "full_record_sensitivity_mm": float(row.full_record_sensitivity_mm),
            "theil_sen_sensitivity_mm": float(row.theil_sen_sensitivity_mm),
        }

    summary: dict[str, object] = {
        "analysis_status": "published-observations-with-incomplete-current-period",
        "source_url": SERIES_URL,
        "source_path": str(bundle.path.relative_to(PROJECT_DIR)) if bundle.path.is_relative_to(PROJECT_DIR) else str(bundle.path),
        "source_sha256": bundle.sha256,
        "source_last_updated": bundle.source_last_updated,
        "first_published_month": bundle.monthly.iloc[0]["date"].strftime("%Y-%m"),
        "last_published_month": bundle.monthly.iloc[-1]["date"].strftime("%Y-%m"),
        "reference_1991_2020_august_july_mm": complete_reference,
        "reference_1991_2020_august_june_mm": partial_reference,
        "complete_period_count": len(complete),
        "latest_complete_period": {
            "period": latest_complete.period,
            "rainfall_total_mm": float(latest_complete.rainfall_total_mm),
            "percentage_of_1991_2020": float(latest_complete.percentage_of_1991_2020),
            "end_year": int(latest_complete.end_year),
        },
        "current_incomplete_period": {
            "period": current_partial.period,
            "months": int(current_partial.months),
            "rainfall_total_mm": float(current_partial.rainfall_total_mm),
            "percentage_of_partial_reference": float(current_partial.percentage_of_partial_reference),
            "wetness_rank": int(current_partial.wetness_rank),
            "comparison_period_count": len(partials),
            "missing_month": "2026-07",
            "complete_period_rank_withheld": True,
        },
        "wettest_complete_periods": wet_rows,
        "driest_complete_periods": dry_rows,
        "annual_reconciliation": {
            "years": len(reconciliation),
            "max_abs_difference_mm": float(reconciliation["difference_mm"].abs().max()),
        },
        "trends": {
            "full_record": full.to_dict(),
            "modern_1970_onward": primary.to_dict(),
            "modern_theil_sen": robust.to_dict(),
        },
        "statistical_projection": {
            "warning": "Illustrative continuation of observed statistical relationships; not a physical climate forecast.",
            "primary_fit": primary.to_dict(),
            "full_record_sensitivity_fit": full.to_dict(),
            "theil_sen_sensitivity_fit": robust.to_dict(),
            "bootstrap_replicates": config.bootstrap_replicates,
            "bootstrap_block_length": config.bootstrap_block_length,
            "random_seed": config.random_seed,
            "milestones": milestones,
        },
        "backtest_summary": {
            "origins": len(backtests),
            "mean_absolute_ten_year_mean_error_mm": float(backtests["ten_year_mean_error_mm"].abs().mean()),
            "mean_annual_mae_mm": float(backtests["annual_mae_mm"].mean()),
            "mean_annual_rmse_mm": float(backtests["annual_rmse_mm"].mean()),
        },
    }

    bundle.monthly.to_csv(DERIVED_DIR / "wales_monthly_rainfall.csv", index=False, float_format="%.6f")
    bundle.annual.to_csv(DERIVED_DIR / "wales_official_annual_and_seasonal_rainfall.csv", index=False, float_format="%.6f")
    reconciliation.to_csv(DERIVED_DIR / "annual_reconciliation.csv", index=False, float_format="%.6f")
    complete.to_csv(DERIVED_DIR / "august_to_july_rainfall.csv", index=False, float_format="%.6f")
    partials.to_csv(DERIVED_DIR / "august_to_june_rainfall.csv", index=False, float_format="%.6f")
    season_trends.to_csv(DERIVED_DIR / "seasonal_trends.csv", index=False, float_format="%.6f")
    projection.to_csv(DERIVED_DIR / "rainfall_statistical_projection.csv", index=False, float_format="%.6f")
    backtests.to_csv(DERIVED_DIR / "backtest_results.csv", index=False, float_format="%.6f")
    (DERIVED_DIR / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    make_history_figure(complete, current_partial, partial_reference, FIGURES_DIR / "wales_august_to_july_rainfall_history", bundle.source_last_updated)
    make_projection_figure(complete, primary, full, robust, projection, FIGURES_DIR / "wales_rainfall_statistical_projection")
    if update_project_readme:
        update_readme(summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--no-update-readme", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.source, update_project_readme=not args.no_update_readme), indent=2))


if __name__ == "__main__":
    main()
