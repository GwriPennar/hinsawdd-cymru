from pathlib import Path
import sys

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from analysis import load_source, sha256  # noqa: E402


def test_source_monthly_contract() -> None:
    bundle = load_source()
    assert bundle.monthly.iloc[0]["date"].strftime("%Y-%m") == "1884-01"
    assert bundle.monthly.iloc[-1]["date"] >= pd.Timestamp("2026-06-01")
    assert not bundle.monthly["date"].duplicated().any()
    assert bundle.source_last_updated is not None


def test_manifest_hash_when_exact_snapshot_is_present() -> None:
    bundle = load_source()
    if bundle.manifest is None:
        return
    assert bundle.manifest["sha256"] == sha256(bundle.path)
    assert bundle.manifest["exact_upstream_bytes"] is True
    assert bundle.manifest["transformation"] == "none"
