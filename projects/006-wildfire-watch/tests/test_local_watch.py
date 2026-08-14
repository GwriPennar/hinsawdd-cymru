from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("local_watch", ROOT / "local_watch.py")
local_watch = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(local_watch)


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "latitude": [51.60, 51.60, 51.80],
            "longitude": [-4.00, -4.00, -4.00],
            "acq_datetime_utc": pd.to_datetime(
                [
                    "2026-08-14T20:00:00Z",
                    "2026-08-14T15:00:00Z",
                    "2026-08-14T20:00:00Z",
                ],
                utc=True,
            ),
            "source": ["VIIRS_SNPP_NRT"] * 3,
        }
    )


def test_filter_recent_keeps_only_bbox_and_time_window():
    now = datetime(2026, 8, 14, 21, 0, tzinfo=timezone.utc)
    result = local_watch.filter_recent(
        _frame(), bbox=local_watch.SWANSEA_GOWER_BBOX, hours=5, now=now
    )
    assert len(result) == 1
    assert result.iloc[0]["latitude"] == 51.60
    assert result.iloc[0]["acq_datetime_utc"].isoformat() == "2026-08-14T20:00:00+00:00"


def test_api_days_rounds_up_and_caps_at_firms_limit():
    assert local_watch._api_days(5) == 1
    assert local_watch._api_days(25) == 2
    assert local_watch._api_days(500) == 5
