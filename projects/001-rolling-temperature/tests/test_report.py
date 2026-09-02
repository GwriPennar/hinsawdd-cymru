from pathlib import Path
import sys

import pytest

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from analysis import AnalysisConfig, run  # noqa: E402


def test_report_summary_contains_full_record_context() -> None:
    summary = run(AnalysisConfig(), update_project_readme=False)

    assert summary["monitor_mode"] == "monthly_rolling_12_month"
    assert summary["current_window"]["period_label"] == "Sep 2025 to Aug 2026"
    assert summary["current_window"]["mean_temperature_c"] == pytest.approx(10.6523287671)
    assert summary["current_window"]["rank_warmest"] == 3
    assert summary["current_window"]["window_count"] == 1701
    assert summary["archived_august_to_july_report"]["rank_among_august_to_july_periods"] == 1

    warmest = summary["top_rolling_12_month_windows"]
    assert len(warmest) == 10
    assert warmest[2]["period_label"] == "Sep 2025 to Aug 2026"


def test_public_report_is_self_contained() -> None:
    report = (PROJECT_DIR / "README.md").read_text(encoding="utf-8")

    required_sections = [
        "## Executive summary",
        "## Monthly monitor charts",
        "## Refresh history",
        "## Historical trend since records began",
        "## Data source and provenance",
        "## Method in plain English",
        "## Validation and confidence",
        "## Limitations",
        "## Reproduce the report",
    ]
    for section in required_sections:
        assert section in report


def test_full_record_graph_contains_trend_context() -> None:
    run(AnalysisConfig(), update_project_readme=False)
    from monthly_monitor import run as run_monthly_monitor

    run_monthly_monitor()
    svg = (
        PROJECT_DIR
        / "figures/wales_rolling_12_month_temperature_history.svg"
    ).read_text(encoding="utf-8")

    assert "rolling 12-month" in svg.lower()
    assert "Trailing 10-window average" in svg
    assert "Derived 1991–2020 reference" in svg
    assert "Previous high" in svg
