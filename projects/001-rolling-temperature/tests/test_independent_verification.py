from decimal import Decimal
from pathlib import Path
import json
import sys

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from analysis import AnalysisConfig, load_source, run  # noqa: E402
from verify import verify  # noqa: E402


def test_independent_verifier_matches_primary() -> None:
    summary = run(AnalysisConfig(), update_project_readme=False)
    summary_path = PROJECT_DIR / "data/derived/summary.json"
    assert json.loads(summary_path.read_text(encoding="utf-8"))["period_mean_central_c"] == summary["period_mean_central_c"]
    bundle = load_source()
    result = verify(
        bundle.path,
        july_2026_c=Decimal("18.0"),
        manifest_path=bundle.path.with_suffix(".provenance.json") if bundle.manifest else None,
        primary_summary_path=summary_path,
    )
    assert result["verification_status"] == "pass"
    assert result["implementation"] == "independent Python standard library and Decimal"
