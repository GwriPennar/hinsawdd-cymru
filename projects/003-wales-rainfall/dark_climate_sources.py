"""Official Met Office fixed-width source parsing."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from dark_climate_constants import (FIELD_SPECS, MONTH_COLUMNS, MONTH_NUMBERS, SEASON_COLUMNS, SourceBundle)

def _fixed_width_rows(text: str) -> list[dict[str, str]]:
    lines = text.splitlines()
    header_index = next((index for index, line in enumerate(lines) if line.lstrip().startswith("year")), None)
    if header_index is None:
        raise ValueError("Could not locate source table header")
    expected = ["year", *MONTH_COLUMNS, *SEASON_COLUMNS, "ann"]
    if re.findall(r"\S+", lines[header_index].lower()) != expected:
        raise ValueError("Unexpected Met Office source columns")
    rows: list[dict[str, str]] = []
    for line in lines[header_index + 1 :]:
        if not re.match(r"^\d{4}\b", line):
            continue
        padded = line.ljust(129)
        rows.append({name: padded[start:end].strip() for name, start, end in FIELD_SPECS})
    if not rows:
        raise ValueError("No source rows parsed")
    return rows


def load_source(path: Path, *, metric: str) -> SourceBundle:
    text = path.read_text(encoding="utf-8")
    expected_descriptions = {
        "rainfall": "Monthly, seasonal and annual total precipitation amount for Wales",
        "raindays1mm": (
            "Monthly, seasonal and annual number of days in the month with precipitation amount >= 1mm for Wales"
        ),
    }
    if metric not in expected_descriptions:
        raise ValueError(f"Unsupported metric: {metric}")
    if (
        "Areal values from HadUK-Grid 1km gridded climate data" not in text
        or expected_descriptions[metric] not in text
    ):
        raise ValueError(f"Not the expected Met Office Wales {metric} source")
    updated = re.search(r"^Last updated\s+(.+)$", text, re.MULTILINE)
    if updated is None:
        raise ValueError("Source Last updated field is missing")
    parsed: list[dict[str, float | int | None]] = []
    for row in _fixed_width_rows(text):
        item: dict[str, float | int | None] = {"year": int(row["year"])}
        for column in [*MONTH_COLUMNS, *SEASON_COLUMNS, "ann"]:
            raw = row[column]
            item[column] = None if raw in {"", "---"} else float(raw)
        parsed.append(item)
    annual = pd.DataFrame(parsed).sort_values("year").reset_index(drop=True)
    monthly_rows: list[dict[str, object]] = []
    for row in parsed:
        year = int(row["year"])
        for month_name in MONTH_COLUMNS:
            raw = row[month_name]
            if raw is None:
                continue
            month = MONTH_NUMBERS[month_name]
            monthly_rows.append(
                {
                    "date": pd.Timestamp(year=year, month=month, day=1),
                    "year": year,
                    "month": month,
                    "month_name": month_name,
                    "value": float(raw),
                }
            )
    monthly = pd.DataFrame(monthly_rows).sort_values("date").reset_index(drop=True)
    expected_dates = pd.date_range(monthly["date"].min(), monthly["date"].max(), freq="MS")
    if not monthly["date"].equals(pd.Series(expected_dates, name="date")):
        raise ValueError(f"Published monthly {metric} coverage is not continuous")
    return SourceBundle(metric, monthly, annual, updated.group(1).strip())
