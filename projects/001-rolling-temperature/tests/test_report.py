from pathlib import Path
import sys

import pytest

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from analysis import AnalysisConfig, run  # noqa: E402


def test_report_summary_contains_full_record_context() -> None:
    summary = run(AnalysisConfig(), update_project_readme=False)

    assert summary["august_to_july_period_count"] == 142
    assert summary["rank_among_august_to_july_periods"] == 1
    assert summary["rank_among_all_monthly_start_12_month_windows"] == 4
    assert summary["trailing_10_period_mean_c"] == pytest.approx(10.0176221274)

    warmest = summary["top_august_to_july_periods"]
    assert len(warmest) == 10
    assert warmest[0]["period"] == "2025-08 to 2026-07"
    assert warmest[1]["period"] == "2006-08 to 2007-07"


def test_public_report_is_self_contained() -> None:
    report = (PROJECT_DIR / "README.md").read_text(encoding="utf-8")

    required_sections = [
        "## Executive summary",
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
    svg = (
        PROJECT_DIR
        / "figures/wales_august_to_july_mean_temperature_provisional.svg"
    ).read_text(encoding="utf-8")

    assert "1884–85 to 2025–26" in svg
    assert "Trailing 10-year average" in svg
    assert "Derived 1991–2020 reference" in svg
    assert "Previous high" in svg
