"""Project 001: Wales August-to-July mean-temperature analysis."""
from __future__ import annotations
import argparse, json, re
from dataclasses import dataclass
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from fetch_source import SERIES_URL, download_source
from source_data import PROJECT_DIR, RAW_DIR, load_source, sha256
from calculations import (all_rolling_12_month_series, annual_reconciliation, august_to_july_series,
    reference_value_for_target_sequence, required_july_to_break_record, sensitivity_table,
    weighted_mean, with_july_2026)

DERIVED_DIR, FIGURES_DIR = PROJECT_DIR / "data/derived", PROJECT_DIR / "figures"
README_PATH = PROJECT_DIR / "README.md"
RESULT_START, RESULT_END = "<!-- BEGIN GENERATED RESULT -->", "<!-- END GENERATED RESULT -->"

@dataclass(frozen=True)
class AnalysisConfig:
    july_2026_scenario_c: float = 18.0
    july_2026_low_c: float = 17.8
    july_2026_high_c: float = 18.3

def make_figure(series: pd.DataFrame, output: Path, july: float, status: str) -> None:
    data = series.copy(); data["ten_period_mean_c"] = data["mean_temperature_c"].rolling(10, min_periods=5).mean()
    sns.set_theme(style="whitegrid", context="notebook"); plt.rcParams.update({"svg.fonttype": "none"})
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.lineplot(data=data, x="end_year", y="mean_temperature_c", ax=ax, linewidth=1.1, label="August-to-July mean")
    sns.lineplot(data=data, x="end_year", y="ten_period_mean_c", ax=ax, linewidth=2.3, label="10-period moving mean")
    current, previous = data.iloc[-1], data.iloc[:-1].nlargest(1, "mean_temperature_c").iloc[0]
    ax.scatter([current.end_year], [current.mean_temperature_c], s=48, zorder=5); ax.axhline(previous.mean_temperature_c, ls="--", lw=.8)
    ax.annotate(f"2025-26: {current.mean_temperature_c:.2f}°C", (current.end_year, current.mean_temperature_c), xytext=(-8, 12), textcoords="offset points", ha="right", fontsize=8)
    ax.set(title="Wales: August-to-July mean temperature", xlabel="Period end year", ylabel="Mean temperature (°C)"); ax.spines[["top", "right"]].set_visible(False)
    label = "published" if status == "published-inputs" else "illustrative scenario"
    fig.text(.01, .01, f"Source: Met Office Wales monthly HadUK-Grid areal series. Months weighted by days. July 2026 = {july:.1f}°C ({label}).", fontsize=6.5)
    fig.tight_layout(rect=(0, .04, 1, 1)); output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output.with_suffix(".svg"), bbox_inches="tight"); fig.savefig(output.with_suffix(".png"), dpi=200, bbox_inches="tight"); plt.close(fig)

def update_readme(summary: dict[str, object]) -> None:
    text = README_PATH.read_text(encoding="utf-8")
    label = "Published July input" if summary["analysis_status"] == "published-inputs" else "Illustrative July scenario"
    note = "The July value is present in the retained source." if summary["analysis_status"] == "published-inputs" else "The exact July Wales area-average is not yet present in the source. This is an **illustrative scenario**, not a Met Office estimate or confidence interval."
    block = f'''{RESULT_START}\n## Current result\n\n| Measure | Result |\n|---|---:|\n| {label} | **{summary["july_2026_value_used_c"]:.1f}°C** |\n| August 2025 to July 2026 mean | **{summary["period_mean_central_c"]:.2f}°C** |\n| Tested scenario range | **{summary["period_mean_scenario_range_c"][0]:.2f}°C to {summary["period_mean_scenario_range_c"][1]:.2f}°C** |\n| Previous August-to-July high | **{summary["previous_august_to_july_record"]["mean_temperature_c"]:.2f}°C** |\n| July value needed to break that high | **{summary["july_2026_mean_needed_to_break_previous_august_to_july_record_c"]:.2f}°C** |\n| Difference from derived 1991-2020 reference | **{summary["anomaly_vs_1991_2020_c"]:+.2f}°C** |\n| August-to-July rank | **{summary["rank_among_august_to_july_periods"]}** |\n\n{note} The ranking is robust because July need only average {summary["july_2026_mean_needed_to_break_previous_august_to_july_record_c"]:.2f}°C to exceed the previous high.\n{RESULT_END}'''
    pattern = re.compile(re.escape(RESULT_START) + r".*?" + re.escape(RESULT_END), re.DOTALL)
    if not pattern.search(text): raise ValueError("README generated-result markers missing")
    README_PATH.write_text(pattern.sub(block, text), encoding="utf-8")

def run(config: AnalysisConfig = AnalysisConfig(), *, refresh: bool = False, source_path: Path | None = None, update_project_readme: bool = True) -> dict[str, object]:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True); FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    if refresh: source_path = download_source(RAW_DIR).source_path
    bundle = load_source(source_path); published = bundle.monthly
    previous = august_to_july_series(published[published["date"] < "2026-07-01"]).nlargest(1, "mean_temperature_c").iloc[0]
    official = published.loc[published["date"] == pd.Timestamp("2026-07-01"), "mean_temperature_c"]
    if official.empty:
        monthly = with_july_2026(published, config.july_2026_scenario_c, "provisional_scenario"); status, july = "provisional-scenario", config.july_2026_scenario_c
    else: monthly, status, july = published, "published-inputs", float(official.iloc[0])
    aug, windows = august_to_july_series(monthly), all_rolling_12_month_series(monthly); current = aug.iloc[-1]
    values = [round(config.july_2026_low_c + i * .1, 1) for i in range(round((config.july_2026_high_c - config.july_2026_low_c) / .1) + 1)]
    sensitivity = sensitivity_table(published, values)
    old_ref = reference_value_for_target_sequence(published, 1961, 1990); new_ref = reference_value_for_target_sequence(published, 1991, 2020)
    required = required_july_to_break_record(published, float(previous.mean_temperature_c)); reconciliation = annual_reconciliation(bundle)
    published.to_csv(DERIVED_DIR / "wales_monthly_mean_temperature.csv", index=False, float_format="%.6f"); aug.to_csv(DERIVED_DIR / "august_to_july_mean_temperature.csv", index=False, float_format="%.6f")
    windows.to_csv(DERIVED_DIR / "all_rolling_12_month_windows.csv", index=False, float_format="%.6f"); sensitivity.to_csv(DERIVED_DIR / "july_2026_sensitivity.csv", index=False, float_format="%.6f")
    reconciliation.to_csv(DERIVED_DIR / "annual_reconciliation.csv", index=False, float_format="%.6f"); make_figure(aug, FIGURES_DIR / "wales_august_to_july_mean_temperature_provisional", july, status)
    current_window = windows[windows["end_month"] == "2026-07-01"].iloc[0]
    summary = {"analysis_status": status, "source": SERIES_URL, "source_path": str(bundle.path.relative_to(PROJECT_DIR)) if bundle.path.is_relative_to(PROJECT_DIR) else str(bundle.path),
        "source_snapshot_kind": bundle.snapshot_kind, "source_snapshot_sha256": sha256(bundle.path), "source_last_updated": bundle.source_last_updated,
        "source_provenance_manifest": str(bundle.path.with_suffix(".provenance.json").relative_to(PROJECT_DIR)) if bundle.manifest else None,
        "period": "2025-08-01 to 2026-07-31", "july_2026_value_used_c": july, "july_2026_value_kind": "published" if status == "published-inputs" else "illustrative_scenario",
        "july_2026_scenario_range_c": [config.july_2026_low_c, config.july_2026_high_c], "period_mean_central_c": float(current.mean_temperature_c),
        "period_mean_scenario_range_c": [float(sensitivity.iloc[0, 1]), float(sensitivity.iloc[-1, 1])], "rank_among_august_to_july_periods": int(current.rank_warmest),
        "previous_august_to_july_record": {"period": str(previous.period), "mean_temperature_c": float(previous.mean_temperature_c)},
        "july_2026_mean_needed_to_break_previous_august_to_july_record_c": required, "anomaly_vs_1961_1990_c": float(current.mean_temperature_c - old_ref),
        "anomaly_vs_1991_2020_c": float(current.mean_temperature_c - new_ref), "derived_reference_1961_1990_c": old_ref, "derived_reference_1991_2020_c": new_ref,
        "rank_among_all_monthly_start_12_month_windows": int(current_window.rank_warmest), "annual_reconciliation_years": int(len(reconciliation)),
        "annual_reconciliation_max_abs_difference_c": float(reconciliation["absolute_difference_c"].max()) if not reconciliation.empty else None,
        "precision_note": "Derived from monthly values rounded to 0.1°C; report headline values to 0.01°C and anomalies approximately."}
    (DERIVED_DIR / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if update_project_readme: update_readme(summary)
    return summary

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__); p.add_argument("--july-2026", type=float, default=18.0); p.add_argument("--july-low", type=float, default=17.8); p.add_argument("--july-high", type=float, default=18.3)
    p.add_argument("--source", type=Path); p.add_argument("--refresh", action="store_true"); p.add_argument("--no-update-readme", action="store_true"); a = p.parse_args()
    print(json.dumps(run(AnalysisConfig(a.july_2026, a.july_low, a.july_high), refresh=a.refresh, source_path=a.source, update_project_readme=not a.no_update_readme), indent=2))
if __name__ == "__main__": main()
