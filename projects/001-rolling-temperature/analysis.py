"""Project 001: Wales August-to-July mean-temperature analysis."""

from __future__ import annotations

import argparse
import calendar
import hashlib
import json
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import pandas as pd
import requests
import seaborn as sns

MONTHS = "jan feb mar apr may jun jul aug sep oct nov dec".split()
PROJECT_DIR = Path(__file__).resolve().parent
SOURCE_PATH = PROJECT_DIR / "data/raw/wales_tmean_monthly_2026-07-01.txt"
DERIVED_DIR = PROJECT_DIR / "data/derived"
FIGURES_DIR = PROJECT_DIR / "figures"
SERIES_URL = "https://www.metoffice.gov.uk/pub/data/weather/uk/climate/datasets/Tmean/date/Wales.txt"
JULY_ARTICLE_URL = (
    "https://www.metoffice.gov.uk/about-us/news-and-media/media-centre/"
    "weather-and-climate-news/2026/an-early-look-at-the-july-statistics-"
    "just-how-dry-has-it-been-"
)


@dataclass(frozen=True)
class AnalysisConfig:
    july_2026_central_c: float = 18.0
    july_2026_low_c: float = 17.8
    july_2026_high_c: float = 18.3


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def download_official_source(path: Path = SOURCE_PATH) -> None:
    response = requests.get(SERIES_URL, timeout=30)
    response.raise_for_status()
    if "Areal values from HadUK-Grid" not in response.text or "year" not in response.text:
        raise ValueError("Downloaded content is not the expected Met Office Wales series")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(response.text, encoding="utf-8")


def load_monthly_source(path: Path = SOURCE_PATH) -> pd.DataFrame:
    lines = path.read_text(encoding="utf-8").splitlines()
    header = next((i for i, line in enumerate(lines) if line.strip().lower().startswith("year")), None)
    if header is None:
        raise ValueError("Could not find the monthly data header")
    wide = pd.read_csv(StringIO("\n".join(lines[header:])), sep=r"\s+", na_values=["NaN", "---"])
    missing = {"year", *MONTHS}.difference(wide.columns)
    if missing:
        raise ValueError(f"Missing source columns: {sorted(missing)}")

    records = []
    for row in wide.itertuples(index=False):
        year = int(row.year)
        for month, name in enumerate(MONTHS, 1):
            value = getattr(row, name)
            if pd.isna(value):
                continue
            records.append({
                "date": pd.Timestamp(year, month, 1),
                "year": year,
                "month": month,
                "mean_temperature_c": float(value),
                "days": calendar.monthrange(year, month)[1],
                "status": "published_monthly_series",
            })
    monthly = pd.DataFrame(records).sort_values("date").reset_index(drop=True)
    if monthly["date"].duplicated().any():
        raise ValueError("Duplicate source months")
    return monthly


def with_july_2026(monthly: pd.DataFrame, value_c: float, status: str) -> pd.DataFrame:
    target = pd.Timestamp("2026-07-01")
    result = monthly[monthly["date"] != target].copy()
    july = pd.DataFrame([{
        "date": target,
        "year": 2026,
        "month": 7,
        "mean_temperature_c": float(value_c),
        "days": 31,
        "status": status,
    }])
    return pd.concat([result, july], ignore_index=True).sort_values("date").reset_index(drop=True)


def weighted_mean(frame: pd.DataFrame) -> float:
    if frame.empty:
        raise ValueError("Cannot calculate an empty mean")
    return float((frame["mean_temperature_c"] * frame["days"]).sum() / frame["days"].sum())


def august_to_july_series(monthly: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for end_year in range(int(monthly["year"].min()) + 1, int(monthly["year"].max()) + 1):
        start = pd.Timestamp(end_year - 1, 8, 1)
        end = pd.Timestamp(end_year, 7, 1)
        window = monthly[(monthly["date"] >= start) & (monthly["date"] <= end)]
        if len(window) != 12:
            continue
        rows.append({
            "period": f"{end_year - 1}-08 to {end_year}-07",
            "start_date": start.date().isoformat(),
            "end_date": pd.Timestamp(end_year, 7, 31).date().isoformat(),
            "end_year": end_year,
            "mean_temperature_c": weighted_mean(window),
            "days": int(window["days"].sum()),
            "status": "provisional" if (window["status"] != "published_monthly_series").any() else "published-inputs",
        })
    result = pd.DataFrame(rows)
    result["rank_warmest"] = result["mean_temperature_c"].rank(method="min", ascending=False).astype(int)
    return result.sort_values("end_year").reset_index(drop=True)


def all_rolling_12_month_series(monthly: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for end in range(11, len(monthly)):
        window = monthly.iloc[end - 11 : end + 1]
        expected = pd.date_range(window.iloc[0]["date"], window.iloc[-1]["date"], freq="MS")
        if not expected.equals(pd.DatetimeIndex(window["date"])):
            continue
        rows.append({
            "start_month": window.iloc[0]["date"].date().isoformat(),
            "end_month": window.iloc[-1]["date"].date().isoformat(),
            "mean_temperature_c": weighted_mean(window),
            "days": int(window["days"].sum()),
            "status": "provisional" if (window["status"] != "published_monthly_series").any() else "published-inputs",
        })
    result = pd.DataFrame(rows)
    result["rank_warmest"] = result["mean_temperature_c"].rank(method="min", ascending=False).astype(int)
    return result


def baseline_for_period(monthly: pd.DataFrame, start_year: int, end_year: int) -> float:
    reference = monthly[monthly["year"].between(start_year, end_year)].copy()
    if reference["year"].nunique() != end_year - start_year + 1:
        raise ValueError("Reference period is incomplete")
    reference["weighted"] = reference["mean_temperature_c"] * reference["days"]
    normals = reference.groupby("month").agg(weighted=("weighted", "sum"), days=("days", "sum"))
    normals["normal_c"] = normals["weighted"] / normals["days"]
    target = pd.date_range("2025-08-01", "2026-07-01", freq="MS")
    weights = [(date.month, calendar.monthrange(date.year, date.month)[1]) for date in target]
    return sum(float(normals.loc[month, "normal_c"]) * days for month, days in weights) / sum(days for _, days in weights)


def required_july_to_break_record(monthly: pd.DataFrame, previous_record_c: float) -> float:
    known = monthly[monthly["date"].between("2025-08-01", "2026-06-01")]
    if len(known) != 11:
        raise ValueError("Expected eleven published months from August 2025 to June 2026")
    known_temperature_days = float((known["mean_temperature_c"] * known["days"]).sum())
    return (previous_record_c * 365 - known_temperature_days) / 31


def sensitivity_table(monthly: pd.DataFrame, values: Iterable[float]) -> pd.DataFrame:
    rows = []
    for value in values:
        current = august_to_july_series(with_july_2026(monthly, value, "provisional_scenario")).iloc[-1]
        rows.append({
            "july_2026_scenario_c": value,
            "aug_2025_to_jul_2026_mean_c": current["mean_temperature_c"],
            "rank_among_aug_to_jul_periods": int(current["rank_warmest"]),
        })
    return pd.DataFrame(rows)


def make_figure(series: pd.DataFrame, output: Path) -> None:
    plot_data = series.copy()
    plot_data["ten_period_mean_c"] = plot_data["mean_temperature_c"].rolling(10, min_periods=5).mean()
    sns.set_theme(style="white", context="notebook")
    plt.rcParams.update({"svg.fonttype": "none", "path.simplify": True, "path.simplify_threshold": 0.8})
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.lineplot(data=plot_data, x="end_year", y="mean_temperature_c", ax=ax, linewidth=1.1)
    sns.lineplot(data=plot_data.iloc[4::5], x="end_year", y="ten_period_mean_c", ax=ax, linewidth=2.5)
    current = plot_data.iloc[-1]
    previous = plot_data.iloc[:-1].nlargest(1, "mean_temperature_c").iloc[0]
    ax.scatter([current.end_year], [current.mean_temperature_c], s=45, zorder=5)
    ax.axhline(previous.mean_temperature_c, linestyle="--", linewidth=0.8)
    ax.text(2023, current.mean_temperature_c + 0.09, f"2025-26 provisional: {current.mean_temperature_c:.2f}°C", ha="right", fontsize=8)
    ax.set(title="Wales: August-to-July mean temperature", xlabel="Period end year", ylabel="Mean temperature (°C)", ylim=(6.8, 10.9))
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.01, "Met Office Wales monthly HadUK-Grid series. Months weighted by days. July 2026 = 18.0°C provisional scenario.", fontsize=6.5)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(output.with_suffix(".png"), dpi=200, bbox_inches="tight")
    plt.close(fig)


def run(config: AnalysisConfig = AnalysisConfig(), refresh: bool = False) -> dict[str, object]:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    if refresh:
        download_official_source()
    published = load_monthly_source()
    previous = august_to_july_series(published[published["date"] < "2026-07-01"]).nlargest(1, "mean_temperature_c").iloc[0]
    official_july = published.loc[published["date"] == pd.Timestamp("2026-07-01"), "mean_temperature_c"]
    if official_july.empty:
        monthly = with_july_2026(published, config.july_2026_central_c, "provisional_central_estimate")
        status, july_used = "provisional", config.july_2026_central_c
    else:
        monthly = published
        status, july_used = "published-inputs", float(official_july.iloc[0])

    aug_jul = august_to_july_series(monthly)
    all_windows = all_rolling_12_month_series(monthly)
    current = aug_jul.iloc[-1]
    values = [round(config.july_2026_low_c + step * 0.1, 1) for step in range(round((config.july_2026_high_c - config.july_2026_low_c) / 0.1) + 1)]
    sensitivity = sensitivity_table(published, values)
    baseline_old = baseline_for_period(published, 1961, 1990)
    baseline_new = baseline_for_period(published, 1991, 2020)
    required_july = required_july_to_break_record(published, float(previous.mean_temperature_c))

    aug_jul.to_csv(DERIVED_DIR / "august_to_july_mean_temperature.csv", index=False, float_format="%.6f")
    all_windows.to_csv(DERIVED_DIR / "all_rolling_12_month_windows.csv", index=False, float_format="%.6f")
    sensitivity.to_csv(DERIVED_DIR / "july_2026_sensitivity.csv", index=False, float_format="%.6f")
    make_figure(aug_jul, FIGURES_DIR / "wales_august_to_july_mean_temperature_provisional")

    current_window = all_windows[all_windows["end_month"] == "2026-07-01"].iloc[0]
    summary = {
        "analysis_status": status,
        "source": SERIES_URL,
        "source_snapshot_sha256": sha256(SOURCE_PATH),
        "source_last_updated": "2026-07-01 11:33",
        "met_office_july_early_look": JULY_ARTICLE_URL,
        "period": "2025-08-01 to 2026-07-31",
        "july_2026_value_used_c": july_used,
        "july_2026_scenario_range_c": [config.july_2026_low_c, config.july_2026_high_c],
        "period_mean_central_c": float(current.mean_temperature_c),
        "period_mean_scenario_range_c": [float(sensitivity.iloc[0, 1]), float(sensitivity.iloc[-1, 1])],
        "rank_among_august_to_july_periods": int(current.rank_warmest),
        "previous_august_to_july_record": {"period": str(previous.period), "mean_temperature_c": float(previous.mean_temperature_c)},
        "july_2026_mean_needed_to_break_previous_august_to_july_record_c": required_july,
        "anomaly_vs_1961_1990_c": float(current.mean_temperature_c - baseline_old),
        "anomaly_vs_1991_2020_c": float(current.mean_temperature_c - baseline_new),
        "baseline_1961_1990_c": baseline_old,
        "baseline_1991_2020_c": baseline_new,
        "rank_among_all_monthly_start_12_month_windows": int(current_window.rank_warmest),
        "precision_note": "Derived from published monthly values rounded to 0.1°C; figures may differ by hundredths from calculations using unrounded grids.",
    }
    (DERIVED_DIR / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--july-2026", type=float, default=18.0)
    parser.add_argument("--july-low", type=float, default=17.8)
    parser.add_argument("--july-high", type=float, default=18.3)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    config = AnalysisConfig(args.july_2026, args.july_low, args.july_high)
    print(json.dumps(run(config, refresh=args.refresh), indent=2))


if __name__ == "__main__":
    main()
