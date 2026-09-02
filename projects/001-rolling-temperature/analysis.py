"""Project 001: Wales rolling 12-month mean-temperature monthly monitor."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from calculations import (
    all_rolling_12_month_series,
    annual_reconciliation,
    august_to_july_series,
    latest_rolling_12_month_window,
    reference_value_for_target_sequence,
    reference_value_for_window,
    required_july_to_break_record,
    sensitivity_table,
    weighted_mean,
    with_july_2026,
)
from fetch_source import SERIES_URL, download_source
from figure_style import (
    LABEL_INDIVIDUAL_PERIODS,
    LABEL_REFERENCE_1991_2020,
    LABEL_TRAILING_AVERAGE,
)
from snapshot_run import refresh_history_table
from source_data import PROJECT_DIR, RAW_DIR, load_source, sha256
from trend_charts import LightTrendConfig, PointAnnotation, render_light_trend

DERIVED_DIR = PROJECT_DIR / "data/derived"
FIGURES_DIR = PROJECT_DIR / "figures"
README_PATH = PROJECT_DIR / "README.md"
RESULT_START = "<!-- BEGIN GENERATED RESULT -->"
RESULT_END = "<!-- END GENERATED RESULT -->"
HISTORY_START = "<!-- BEGIN REFRESH HISTORY -->"
HISTORY_END = "<!-- END REFRESH HISTORY -->"


@dataclass(frozen=True)
class AnalysisConfig:
    july_2026_scenario_c: float = 18.0
    july_2026_low_c: float = 17.8
    july_2026_high_c: float = 18.3


def make_figure(
    series: pd.DataFrame,
    output: Path,
    july: float,
    status: str,
    reference_1991_2020_c: float,
) -> None:
    """Create the archived August-to-July full-record trend graphic."""

    data = series.copy()
    data["trailing_10_period_mean_c"] = (
        data["mean_temperature_c"].rolling(10, min_periods=10).mean()
    )
    current = data.iloc[-1]
    previous = data.iloc[:-1].nlargest(1, "mean_temperature_c").iloc[0]
    current_label = "published" if status == "published-inputs" else "illustrative"
    july_label = "published input" if status == "published-inputs" else "illustrative scenario"
    render_light_trend(
        data,
        output,
        reference_c=reference_1991_2020_c,
        config=LightTrendConfig(
            title="Wales August-to-July mean temperature, 1884–85 to 2025–26",
            xlabel="Period end year",
            ylabel="Mean temperature (°C)",
            footer=(
                "Source: Met Office Wales monthly HadUK-Grid areal series. "
                "Monthly means are weighted by calendar days. "
                f"July 2026 = {july:.1f}°C ({july_label})."
            ),
            label_individual=LABEL_INDIVIDUAL_PERIODS,
            label_average=LABEL_TRAILING_AVERAGE,
            label_reference=LABEL_REFERENCE_1991_2020,
            x_col="end_year",
            y_col="mean_temperature_c",
            trailing_col="trailing_10_period_mean_c",
            previous=PointAnnotation(
                float(previous.end_year),
                float(previous.mean_temperature_c),
                f"Previous high\n2006–07: {previous.mean_temperature_c:.2f}°C",
            ),
            current=PointAnnotation(
                float(current.end_year),
                float(current.mean_temperature_c),
                f"2025–26 {current_label}\n{current.mean_temperature_c:.2f}°C",
                xytext=(-10, 18),
            ),
            xlim_pad=2.0,
        ),
    )


def _warmest_windows_table(summary: dict[str, object]) -> str:
    rows = [
        "| Rank | 12-month window | Mean temperature | Status |",
        "|---:|---|---:|---|",
    ]
    for item in summary["top_rolling_12_month_windows"]:
        rows.append(
            "| {rank} | {period} | **{mean:.2f}°C** | {status} |".format(
                rank=item["rank"],
                period=item["period_label"],
                mean=item["mean_temperature_c"],
                status=item["status"],
            )
        )
    return "\n".join(rows)


def _warmest_periods_table(summary: dict[str, object]) -> str:
    rows = [
        "| Rank | August-to-July period | Mean temperature | Status |",
        "|---:|---|---:|---|",
    ]
    for item in summary["top_august_to_july_periods"]:
        rows.append(
            "| {rank} | {period} | **{mean:.2f}°C** | {status} |".format(
                rank=item["rank"],
                period=item["period"],
                mean=item["mean_temperature_c"],
                status=item["status"],
            )
        )
    return "\n".join(rows)


def update_readme(summary: dict[str, object]) -> None:
    """Refresh the machine-generated results section of the public report."""

    text = README_PATH.read_text(encoding="utf-8")
    current = summary["current_window"]
    published = summary["analysis_status"] == "published-inputs"
    last_month = pd.Timestamp(str(summary.get("last_published_month", "2026-08")) + "-01").strftime("%B %Y")
    warmest_table = _warmest_windows_table(summary)
    archived = summary["archived_august_to_july_report"]

    block = f"""{RESULT_START}
## Headline results

**Status:** {'Published-input calculation' if published else 'Provisional calculation using incomplete monthly inputs'}
**Monitor cadence:** Monthly refresh on published Met Office Wales monthly data
**Latest complete window:** **{current['period_label']}**

| Measure | Result |
|---|---:|
| Published source coverage | **January 1884 to {last_month}** |
| Latest 12-month mean | **{current['mean_temperature_c']:.2f}°C** |
| Rank among all monthly-start 12-month windows | **{current['rank_warmest']} of {current['window_count']}** |
| Previous record window | **{summary['previous_rolling_12_month_record']['mean_temperature_c']:.2f}°C**, {summary['previous_rolling_12_month_record']['period_label']} |
| Margin over previous record | **{summary['margin_over_previous_rolling_record_c']:+.2f}°C** |
| Difference from derived 1991–2020 reference | **{summary['anomaly_vs_1991_2020_c']:+.2f}°C** |
| Difference from derived 1961–1990 reference | **{summary['anomaly_vs_1961_1990_c']:+.2f}°C** |
| Current trailing 10-window average | **{summary['trailing_10_window_mean_c']:.2f}°C** |

The headline window ends on the **last published calendar month** in the retained Met Office source ({last_month}). Each refresh advances the window by one month when a new monthly value is published.

### Archived August-to-July report

The original August-to-July 2025–26 research question is preserved in [`archive/august-to-july-2025-26/`](archive/august-to-july-2025-26/ARCHIVE.md): warmest equivalent August-to-July period at **{archived['period_mean_c']:.2f}°C** ({archived['rank_among_august_to_july_periods']} of {archived['august_to_july_period_count']}).

### Ten warmest rolling 12-month windows

{warmest_table}
{RESULT_END}"""

    pattern = re.compile(
        re.escape(RESULT_START) + r".*?" + re.escape(RESULT_END),
        re.DOTALL,
    )
    if not pattern.search(text):
        raise ValueError("README generated-result markers missing")
    text = pattern.sub(block, text)

    history_block = f"""{HISTORY_START}
## Refresh history

Each monthly refresh is frozen under [`runs/`](runs/index.json). The table below lists isolated run folders; live `figures/` always shows the latest refresh.

{refresh_history_table()}
{HISTORY_END}"""
    history_pattern = re.compile(
        re.escape(HISTORY_START) + r".*?" + re.escape(HISTORY_END),
        re.DOTALL,
    )
    if history_pattern.search(text):
        text = history_pattern.sub(history_block, text)
    elif "<!-- END GENERATED RESULT -->" in text:
        text = text.replace(
            "<!-- END GENERATED RESULT -->",
            "<!-- END GENERATED RESULT -->\n\n" + history_block,
            1,
        )
    README_PATH.write_text(text, encoding="utf-8")


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
    previous = august_to_july_series(
        published[published["date"] < "2026-07-01"]
    ).nlargest(1, "mean_temperature_c").iloc[0]

    official = published.loc[
        published["date"] == pd.Timestamp("2026-07-01"),
        "mean_temperature_c",
    ]
    if official.empty:
        monthly = with_july_2026(
            published,
            config.july_2026_scenario_c,
            "provisional_scenario",
        )
        status = "provisional-scenario"
        july = config.july_2026_scenario_c
    else:
        monthly = published
        status = "published-inputs"
        july = float(official.iloc[0])

    august_july = august_to_july_series(monthly)
    rolling = all_rolling_12_month_series(monthly)
    current_window = latest_rolling_12_month_window(monthly)
    current_aug_jul = august_july.iloc[-1]
    window_frame = monthly[
        monthly["date"].between(current_window.start_month, current_window.end_month)
    ]

    values = [
        round(config.july_2026_low_c + i * 0.1, 1)
        for i in range(
            round(
                (config.july_2026_high_c - config.july_2026_low_c) / 0.1
            )
            + 1
        )
    ]
    sensitivity = sensitivity_table(published, values)
    aug_jul_old_reference = reference_value_for_target_sequence(monthly, 1961, 1990)
    aug_jul_new_reference = reference_value_for_target_sequence(monthly, 1991, 2020)
    old_reference = reference_value_for_window(monthly, 1961, 1990, window_frame)
    new_reference = reference_value_for_window(monthly, 1991, 2020, window_frame)
    required_july = required_july_to_break_record(
        published,
        float(previous.mean_temperature_c),
    )
    reconciliation = annual_reconciliation(bundle)
    previous_window = rolling.iloc[:-1].nlargest(1, "mean_temperature_c").iloc[0]
    top_windows = rolling.nlargest(10, "mean_temperature_c")
    trailing_10 = float(rolling["mean_temperature_c"].tail(10).mean())

    published.to_csv(
        DERIVED_DIR / "wales_monthly_mean_temperature.csv",
        index=False,
        float_format="%.6f",
    )
    august_july.to_csv(
        DERIVED_DIR / "august_to_july_mean_temperature.csv",
        index=False,
        float_format="%.6f",
    )
    rolling.to_csv(
        DERIVED_DIR / "rolling_12_month_mean_temperature.csv",
        index=False,
        float_format="%.6f",
    )
    rolling.to_csv(
        DERIVED_DIR / "all_rolling_12_month_windows.csv",
        index=False,
        float_format="%.6f",
    )
    sensitivity.to_csv(
        DERIVED_DIR / "july_2026_sensitivity.csv",
        index=False,
        float_format="%.6f",
    )
    reconciliation.to_csv(
        DERIVED_DIR / "annual_reconciliation.csv",
        index=False,
        float_format="%.6f",
    )

    current_window_rank = int(current_window.rank_warmest)
    summary = {
        "monitor_mode": "monthly_rolling_12_month",
        "analysis_status": status,
        "source": SERIES_URL,
        "source_path": (
            str(bundle.path.relative_to(PROJECT_DIR))
            if bundle.path.is_relative_to(PROJECT_DIR)
            else str(bundle.path)
        ),
        "source_snapshot_kind": bundle.snapshot_kind,
        "source_snapshot_sha256": sha256(bundle.path),
        "source_last_updated": bundle.source_last_updated,
        "last_published_month": bundle.monthly.iloc[-1]["date"].strftime("%Y-%m"),
        "source_provenance_manifest": (
            str(
                bundle.path.with_suffix(".provenance.json").relative_to(
                    PROJECT_DIR
                )
            )
            if bundle.manifest
            else None
        ),
        "current_window": {
            "start_month": str(current_window.start_month),
            "end_month": str(current_window.end_month),
            "period_label": str(current_window.period_label),
            "mean_temperature_c": float(current_window.mean_temperature_c),
            "rank_warmest": current_window_rank,
            "window_count": int(len(rolling)),
            "status": (
                "published inputs"
                if current_window.status == "published-inputs"
                else "illustrative scenario"
            ),
        },
        "previous_rolling_12_month_record": {
            "period_label": str(previous_window.period_label),
            "start_month": str(previous_window.start_month),
            "end_month": str(previous_window.end_month),
            "mean_temperature_c": float(previous_window.mean_temperature_c),
        },
        "margin_over_previous_rolling_record_c": float(
            current_window.mean_temperature_c - previous_window.mean_temperature_c
        ),
        "anomaly_vs_1961_1990_c": float(
            current_window.mean_temperature_c - old_reference
        ),
        "anomaly_vs_1991_2020_c": float(
            current_window.mean_temperature_c - new_reference
        ),
        "derived_reference_1961_1990_c": old_reference,
        "derived_reference_1991_2020_c": new_reference,
        "august_to_july_reference_1961_1990_c": aug_jul_old_reference,
        "august_to_july_reference_1991_2020_c": aug_jul_new_reference,
        "trailing_10_window_mean_c": trailing_10,
        "top_rolling_12_month_windows": [
            {
                "rank": int(row.rank_warmest),
                "period_label": str(row.period_label),
                "start_month": str(row.start_month),
                "end_month": str(row.end_month),
                "mean_temperature_c": float(row.mean_temperature_c),
                "status": (
                    "illustrative scenario"
                    if row.status == "provisional-scenario"
                    else "published inputs"
                ),
            }
            for row in top_windows.itertuples(index=False)
        ],
        "archived_august_to_july_report": {
            "archive_path": "archive/august-to-july-2025-26/",
            "period": "2025-08-01 to 2026-07-31",
            "period_mean_c": float(current_aug_jul.mean_temperature_c),
            "rank_among_august_to_july_periods": int(current_aug_jul.rank_warmest),
            "august_to_july_period_count": int(len(august_july)),
            "july_2026_value_used_c": july,
        },
        "period_mean_central_c": float(current_window.mean_temperature_c),
        "rank_among_all_monthly_start_12_month_windows": current_window_rank,
        "august_to_july_period_count": int(len(august_july)),
        "rank_among_august_to_july_periods": int(current_aug_jul.rank_warmest),
        "previous_august_to_july_record": {
            "period": str(previous.period),
            "mean_temperature_c": float(previous.mean_temperature_c),
        },
        "margin_over_previous_record_c": float(
            current_aug_jul.mean_temperature_c - previous.mean_temperature_c
        ),
        "july_2026_value_used_c": july,
        "july_2026_value_kind": (
            "published" if status == "published-inputs" else "illustrative_scenario"
        ),
        "july_2026_mean_needed_to_break_previous_august_to_july_record_c": required_july,
        "period_mean_scenario_range_c": [
            float(sensitivity.iloc[0, 1]),
            float(sensitivity.iloc[-1, 1]),
        ],
        "trailing_10_period_mean_c": float(
            august_july["mean_temperature_c"].tail(10).mean()
        ),
        "top_august_to_july_periods": [
            {
                "rank": int(row.rank_warmest),
                "period": str(row.period),
                "mean_temperature_c": float(row.mean_temperature_c),
                "status": (
                    "illustrative scenario"
                    if row.status == "provisional-scenario"
                    else "published inputs"
                ),
            }
            for row in august_july.nlargest(10, "mean_temperature_c").itertuples(index=False)
        ],
        "annual_reconciliation_years": int(len(reconciliation)),
        "annual_reconciliation_max_abs_difference_c": (
            float(reconciliation["absolute_difference_c"].max())
            if not reconciliation.empty
            else None
        ),
        "precision_note": (
            "Derived from monthly values rounded to 0.1°C; report headline values "
            "to 0.01°C and anomalies approximately."
        ),
    }

    (DERIVED_DIR / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    if update_project_readme:
        update_readme(summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--july-2026", type=float, default=18.0)
    parser.add_argument("--july-low", type=float, default=17.8)
    parser.add_argument("--july-high", type=float, default=18.3)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--no-update-readme", action="store_true")
    args = parser.parse_args()

    summary = run(
        AnalysisConfig(
            args.july_2026,
            args.july_low,
            args.july_high,
        ),
        refresh=args.refresh,
        source_path=args.source,
        update_project_readme=not args.no_update_readme,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
