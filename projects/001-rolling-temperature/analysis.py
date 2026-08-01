"""Project 001: Wales August-to-July mean-temperature analysis."""

from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import re
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from fetch_source import SERIES_URL, download_source

MONTHS = "jan feb mar apr may jun jul aug sep oct nov dec".split()
PROJECT_DIR = Path(__file__).resolve().parent
RAW_DIR = PROJECT_DIR / "data/raw"
LEGACY_SOURCE_PATH = RAW_DIR / "wales_tmean_monthly_2026-07-01.txt"
DERIVED_DIR = PROJECT_DIR / "data/derived"
FIGURES_DIR = PROJECT_DIR / "figures"
README_PATH = PROJECT_DIR / "README.md"
JULY_ARTICLE_URL = (
    "https://www.metoffice.gov.uk/about-us/news-and-media/media-centre/"
    "weather-and-climate-news/2026/an-early-look-at-the-july-statistics-"
    "just-how-dry-has-it-been-"
)
RESULT_START = "<!-- BEGIN GENERATED RESULT -->"
RESULT_END = "<!-- END GENERATED RESULT -->"
LAST_UPDATED_RE = re.compile(r"^(?:Last updated|Source last updated:)\s*(.+)$", re.MULTILINE)


@dataclass(frozen=True)
class AnalysisConfig:
    july_2026_scenario_c: float = 18.0
    july_2026_low_c: float = 17.8
    july_2026_high_c: float = 18.3


@dataclass(frozen=True)
class SourceBundle:
    path: Path
    monthly: pd.DataFrame
    annual: pd.DataFrame
    source_last_updated: str | None
    snapshot_kind: str
    manifest: dict[str, object] | None


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def latest_source_path() -> Path:
    exact = sorted(RAW_DIR.glob("metoffice-wales-tmean-retrieved-*.txt"))
    if exact:
        return exact[-1]
    if LEGACY_SOURCE_PATH.exists():
        return LEGACY_SOURCE_PATH
    raise FileNotFoundError("No Met Office source snapshot is available")


def _manifest_for(path: Path) -> dict[str, object] | None:
    manifest_path = path.with_suffix(".provenance.json")
    if not manifest_path.exists():
        return None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("sha256") != sha256(path):
        raise ValueError(f"Source hash does not match provenance manifest: {manifest_path}")
    return manifest


def load_source(path: Path | None = None) -> SourceBundle:
    source_path = path or latest_source_path()
    text = source_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    header = next((i for i, line in enumerate(lines) if line.strip().lower().startswith("year")), None)
    if header is None:
        raise ValueError("Could not find the source data header")
    table_text = "\n".join(lines[header:])
    header_line = lines[header]
    header_matches = list(re.finditer(r"\S+", header_line))
    header_names = [match.group(0) for match in header_matches]
    if "ann" in header_names:
        ends = [match.end() for match in header_matches]
        colspecs = [(0 if index == 0 else ends[index - 1], ends[index]) for index in range(len(ends))]
        rows = []
        for raw in lines[header + 1 :]:
            fields = [raw[start:end].strip() for start, end in colspecs]
            if not fields or not fields[0].lstrip("-").isdigit():
                continue
            rows.append(fields)
        wide = pd.DataFrame(rows, columns=header_names).replace({"": pd.NA, "NaN": pd.NA, "---": pd.NA})
        for column in wide.columns:
            wide[column] = pd.to_numeric(wide[column], errors="coerce")
    else:
        # Compatibility with the repository's original normalized transcription.
        wide = pd.read_csv(StringIO(table_text), sep=r"\s+", na_values=["NaN", "---"])
    missing = {"year", *MONTHS}.difference(wide.columns)
    if missing:
        raise ValueError(f"Missing source columns: {sorted(missing)}")


    records: list[dict[str, object]] = []
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
    if monthly.empty or monthly["date"].duplicated().any():
        raise ValueError("Source monthly series is empty or contains duplicate months")
    expected = pd.date_range(monthly.iloc[0]["date"], monthly.iloc[-1]["date"], freq="MS")
    if not expected.equals(pd.DatetimeIndex(monthly["date"])):
        raise ValueError("Published monthly series contains an unexpected gap")

    annual = pd.DataFrame(columns=["year", "official_annual_mean_c"])
    if "ann" in wide.columns:
        annual = (
            wide.loc[wide["ann"].notna(), ["year", "ann"]]
            .rename(columns={"ann": "official_annual_mean_c"})
            .astype({"year": int, "official_annual_mean_c": float})
            .reset_index(drop=True)
        )

    match = LAST_UPDATED_RE.search(text)
    source_last_updated = match.group(1).strip() if match else None
    manifest = _manifest_for(source_path)
    snapshot_kind = "exact_upstream_snapshot" if manifest and manifest.get("exact_upstream_bytes") is True else "legacy_normalized_snapshot"
    return SourceBundle(source_path, monthly, annual, source_last_updated, snapshot_kind, manifest)


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
    rows: list[dict[str, object]] = []
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
            "status": "provisional-scenario" if (window["status"] != "published_monthly_series").any() else "published-inputs",
        })
    result = pd.DataFrame(rows)
    result["rank_warmest"] = result["mean_temperature_c"].rank(method="min", ascending=False).astype(int)
    return result.sort_values("end_year").reset_index(drop=True)


def all_rolling_12_month_series(monthly: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
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
            "status": "provisional-scenario" if (window["status"] != "published_monthly_series").any() else "published-inputs",
        })
    result = pd.DataFrame(rows)
    result["rank_warmest"] = result["mean_temperature_c"].rank(method="min", ascending=False).astype(int)
    return result


def reference_value_for_target_sequence(monthly: pd.DataFrame, start_year: int, end_year: int) -> float:
    reference = monthly[monthly["year"].between(start_year, end_year)].copy()
    expected_rows = (end_year - start_year + 1) * 12
    if len(reference) != expected_rows:
        raise ValueError(f"Reference period is incomplete: expected {expected_rows} months, found {len(reference)}")
    # HadUK-Grid climatologies average the corresponding monthly grids over the reference years.
    monthly_normals = reference.groupby("month")["mean_temperature_c"].mean()
    target = pd.date_range("2025-08-01", "2026-07-01", freq="MS")
    weights = [(date.month, calendar.monthrange(date.year, date.month)[1]) for date in target]
    return sum(float(monthly_normals.loc[month]) * days for month, days in weights) / sum(days for _, days in weights)


def annual_reconciliation(bundle: SourceBundle) -> pd.DataFrame:
    if bundle.annual.empty:
        return pd.DataFrame(columns=["year", "derived_from_rounded_months_c", "official_annual_mean_c", "difference_c", "absolute_difference_c"])
    rows: list[dict[str, object]] = []
    for record in bundle.annual.itertuples(index=False):
        year_frame = bundle.monthly[bundle.monthly["year"] == int(record.year)]
        if len(year_frame) != 12:
            continue
        derived = weighted_mean(year_frame)
        difference = derived - float(record.official_annual_mean_c)
        rows.append({
            "year": int(record.year),
            "derived_from_rounded_months_c": derived,
            "official_annual_mean_c": float(record.official_annual_mean_c),
            "difference_c": difference,
            "absolute_difference_c": abs(difference),
        })
    return pd.DataFrame(rows)


def required_july_to_break_record(monthly: pd.DataFrame, previous_record_c: float) -> float:
    known = monthly[monthly["date"].between("2025-08-01", "2026-06-01")]
    if len(known) != 11:
        raise ValueError("Expected eleven published months from August 2025 to June 2026")
    known_temperature_days = float((known["mean_temperature_c"] * known["days"]).sum())
    return (previous_record_c * 365 - known_temperature_days) / 31


def sensitivity_table(monthly: pd.DataFrame, values: Iterable[float]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for value in values:
        current = august_to_july_series(with_july_2026(monthly, value, "provisional_scenario")).iloc[-1]
        rows.append({
            "july_2026_scenario_c": value,
            "aug_2025_to_jul_2026_mean_c": current["mean_temperature_c"],
            "rank_among_aug_to_jul_periods": int(current["rank_warmest"]),
        })
    return pd.DataFrame(rows)


def make_figure(series: pd.DataFrame, output: Path, *, july_value_c: float, analysis_status: str) -> None:
    plot_data = series.copy()
    plot_data["ten_period_mean_c"] = plot_data["mean_temperature_c"].rolling(10, min_periods=5).mean()
    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams.update({"svg.fonttype": "none", "path.simplify": True, "path.simplify_threshold": 0.8})
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.lineplot(data=plot_data, x="end_year", y="mean_temperature_c", ax=ax, linewidth=1.1, label="Annual August-to-July mean")
    sns.lineplot(data=plot_data, x="end_year", y="ten_period_mean_c", ax=ax, linewidth=2.3, label="10-period moving mean")
    current = plot_data.iloc[-1]
    previous = plot_data.iloc[:-1].nlargest(1, "mean_temperature_c").iloc[0]
    ax.scatter([current.end_year], [current.mean_temperature_c], s=48, zorder=5)
    ax.axhhline(previous.mean_temperature_c, linestyle="--", linewidth=0.8)
    ax.annotate(
        f"2025-26: {current.mean_temperature_c:.2f}°C",
        xy=(current.end_year, current.mean_temperature_c),
        xytext=(-8, 12),
        textcoords="offset points",
        ha="right",
        fontsize=8,
    )
    ax.set(title="Wales: August-to-July mean temperature", xlabel="Period end year", ylabel="Mean temperature (°C)")
    ax.spines[["top", "right"]].set_visible(False)
    july_label = "published" if analysis_status == "published-inputs" else "illustrative scenario"
    fig.text(
        0.01,
        0.01,
        f"Source: Met Office Wales monthly HadUK-Grid areal series. Months weighted by days. July 2026 = {july_value_c:.1f}°C ({july_label}).",
        fontsize=6.5,
    )
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(output.with_suffix(".png"), dpi=200, bbox_inches="tight")
    plt.close(fig)


def _render_generated_result(summary: dict[str, object]) -> str:
    scenario = summary["july_2026_value_used_c"]
    label = "Published July input" if summary["analysis_status"] == "published-inputs" else "Illustrative July scenario"
    return f"""{RESULT_START}
## Current result

| Measure | Result |
|---|---:|
| {label} | **{scenario:.1f}°C** |
| August 2025 to July 2026 mean | **{summary['period_mean_central_c']:.2f}°C** |
| Tested scenario range | **{summary['period_mean_scenario_range_c'][0]:.2f}°C to {summary['period_mean_scenario_range_c'][1]:.2f}°C** |
| Previous August-to-July high | **{summary['previous_august_to_july_record']['mean_temperature_c']:.2f}°C** |
| July value needed to break that high | **{summary['july_2026_mean_needed_to_break_previous_august_to_july_record_c']:.2f}°C** |
| Difference from derived 1991-2020 reference | **{summary['anomaly_vs_1991_2020_c']:+.2f}°C** |
| August-to-July rank | **{summary['rank_among_august_to_july_periods']}** |

The exact July Wales area-average is not yet present in the monthly source series. The value above is an **illustrative scenario**, not a Met Office estimate or a confidence interval. The record ranking is nevertheless robust because July would only need to average {summary['july_2026_mean_needed_to_break_previous_august_to_july_record_c']:.2f}°C to exceed the previous August-to-July high.
{RESULT_END}"""


def update_readme(summary: dict[str, object], path: Path = README_PATH) -> None:
    text = path.read_text(encoding="utf-8")
    replacement = _render_generated_result(summary)
    pattern = re.compile(re.escape(RESULT_START) + r".*?" + re.escape(RESULT_END), re.DOTALL)
    if not pattern.search(text):
        raise ValueError("README does not contain generated-result markers")
    path.write_text(pattern.sub(replacement, text) + ("" if text.endswith("\n") else "\n"), encoding="utf-8")


def run(
    config: AnalysisConfig = AnalysisConfig(),
    *,
    refresh: bool = False,
    source_path: Path | None = None,
    update_project_readme: bool = True,
) -> dict[str, object]:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    if refresh:
        source_path = download_source(RAW_DIR).source_path
    bundle = load_source(source_path)
    published = bundle.monthly
    previous = august_to_july_series(published[published["date"] < "2026-07-01"]).nlargest(1, "mean_temperature_c").iloc[0]
    official_july = published.loc[published["date"] == pd.Timestamp("2026-07-01"), "mean_temperature_c"]
    if official_july.empty:
        monthly = with_july_2026(published, config.july_2026_scenario_c, "provisional_scenario")
        status, july_used = "provisional-scenario", config.july_2026_scenario_c
    else:
        monthly = published
        status, july_used = "published-inputs", float(official_july.iloc[0])

    aug_jul = august_to_july_series(monthly)
    all_windows = all_rolling_12_month_series(monthly)
    current = aug_jul.iloc[-1]
    values = [round(config.july_2026_low_c + step * 0.1, 1) for step in range(round((config.july_2026_high_c - config.july_2026_low_c) / 0.1) + 1)]
    sensitivity = sensitivity_table(published, values)
    baseline_old = reference_value_for_target_sequence(published, 1961, 1990)
    baseline_new = reference_value_for_target_sequence(published, 1991, 2020)
    required_july = required_july_to_break_record(published, float(previous.mean_temperature_c))
    reconciliation = annual_reconciliation(bundle)

    published.to_csv(DERIVED_DIR / "wales_monthly_mean_temperature.csv", index=False, float_format="%.6f")
    aug_jul.to_csv(DERIVED_DIR / "august_to_july_mean_temperature.csv", index=False, float_format="%.6f")
    all_windows.to_csv(DERIVED_DIR / "all_rolling_12_month_windows.csv", index=False, float_format="%.6f")
    sensitivity.to_csv(DERIVED_DIR / "july_2026_sensitivity.csv", index=False, float_format="%.6f")
    reconciliation.to_csv(DERIVED_DIR / "annual_reconciliation.csv", index=False, float_format="%.6f")
    figure_stem = FIGURES_DIR / "wales_august_to_july_mean_temperature_provisional"
    make_figure(aug_jul, figure_stem, july_value_c=july_used, analysis_status=status)

    current_window = all_windows[all_windows["end_month"] == "2026-07-01"].iloc[0]
    max_annual_difference = float(reconciliation["absolute_difference_c"].max()) if not reconciliation.empty else None
    summary: dict[str, object] = {
        "analysis_status": status,
        "source": SERIES _URL,
        "source_path": str(bundle.path.relative_to(PROJECT_DIR)) if bundle.path.is_relative_to(PROJECT_DIR) else str(bundle.path),
        "source_snapshot_kind": bundle.snapshot_kind,
        "source_snapshot_sha256": sha256(bundle.path),
        "source_last_updated": bundle.source_last_updated,
        "source_provenance_manifest": str(bundle.path.with_suffix(".provenance.json").relative_to(PROJECT_DIR)) if bundle.manifest else None,
        "met_office_july_early_look": JULY_ARTICLE_URL,
        "period": "2025-08-01 to 2026-07-31",
        "july_2026_value_used_c": july_used,
        "july_2026_value_kind": "published" if status == "published-inputs" else "illustrative_scenario",
        "july_2026_scenario_range_c": [config.july_2026_low_c, config.july_2026_high_c],
        "period_mean_central_c": float(current.mean_temperature_c),
        "period_mean_scenario_range_c": [float(sensitivity.iloc[0, 1]), float(sensitivity.iloc[-1, 1])],
        "rank_among_august_to_july_periods": int(current.rank_warmest),
        "previous_august_to_july_record": {"period": str(previous.period), "mean_temperature_c": float(previous.mean_temperature_c)},
        "july_2026_mean_needed_to_break_previous_august_to_july_record_c": required_july,
        "anomaly_vs_1961_1990_c": float(current.mean_temperature_c - baseline_old),
        "anomaly_vs_1991_2020_c": float(current.mean_temperature_c - baseline_new),
        "derived_reference_1961_1990_c": baseline_old,
        "derived_reference_1991_2020_c": baseline_new,
        "rank_among_all_monthly_start_12_month_windows": int(current_window.rank_warmest),
        "annual_reconciliation_years": int(len(reconciliation)),
        "annual_reconciliation_max_abs_difference_c": max_annual_difference,
        "precision_note": "Derived from published monthly values rounded to 0.1°C; report headline values to 0.01°C and anomalies approximately.",
    }
    (DERIVED_DIR / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if update_project_readme:
        update_readme(summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--july-2026", type=float, default=18.0, help="Illustrative July scenario until an official value is published")
    parser.add_argument("--july-low", type=float, default=17.8)
    parser.add_argument("--july-high", type=float, default=18.3)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--no-update-readme", action="store_true")
    args = parser.parse_args()
    config = AnalysisConfig(args.july_2026, args.july_low, args.july_high)
    print(json.dumps(run(
        config,
        refresh=args.refresh,
        source_path=args.source,
        update_project_readme=not args.no_update_readme,
    ), indent=2))


if __name__ == "__main__":
    main()
