"""Independent standard-library and Decimal verification for Project 003."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec = 50
PROJECT_DIR = Path(__file__).resolve().parent
RAW_DIR = PROJECT_DIR / "data/raw"
DERIVED_DIR = PROJECT_DIR / "data/derived"
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
MONTH_NUMBER = {name: index for index, name in enumerate(MONTHS, start=1)}


def discover_source() -> Path:
    candidates = sorted(RAW_DIR.glob("metoffice-wales-rainfall-source-*.txt"))
    if not candidates:
        candidates = sorted(RAW_DIR.glob("metoffice-wales-rainfall-retrieved-*.txt"))
    if not candidates:
        raise FileNotFoundError("No Project 003 rainfall source snapshot found")
    return candidates[-1]


def parse_fixed_width(path: Path) -> tuple[dict[tuple[int, int], Decimal], dict[int, Decimal], str]:
    text = path.read_text(encoding="utf-8")
    if "Monthly, seasonal and annual total precipitation amount for Wales" not in text:
        raise ValueError("Unexpected source content")
    last_updated_match = re.search(r"^Last updated\s+(.+)$", text, re.MULTILINE)
    if last_updated_match is None:
        raise ValueError("Missing Last updated field")
    lines = text.splitlines()
    header_index = next(i for i, line in enumerate(lines) if line.lstrip().startswith("year"))
    matches = list(re.finditer(r"\S+", lines[header_index]))
    columns = [match.group(0).lower() for match in matches]
    starts = [match.start() for match in matches]
    monthly: dict[tuple[int, int], Decimal] = {}
    annual: dict[int, Decimal] = {}

    for line in lines[header_index + 1 :]:
        if not re.match(r"^\s*\d{4}\b", line):
            continue
        values: dict[str, str] = {}
        for index, column in enumerate(columns):
            end = starts[index + 1] if index + 1 < len(starts) else None
            values[column] = line[starts[index] : end].strip()
        year = int(values["year"])
        for name in MONTHS:
            raw = values[name]
            if raw not in {"", "---"}:
                monthly[(year, MONTH_NUMBER[name])] = Decimal(raw)
        if values["ann"] not in {"", "---"}:
            annual[year] = Decimal(values["ann"])
    return monthly, annual, last_updated_match.group(1).strip()


def period_total(monthly: dict[tuple[int, int], Decimal], end_year: int, months: int, end_month: int) -> Decimal | None:
    end_index = end_year * 12 + end_month - 1
    keys: list[tuple[int, int]] = []
    for offset in range(months - 1, -1, -1):
        index = end_index - offset
        year, zero_month = divmod(index, 12)
        keys.append((year, zero_month + 1))
    if not all(key in monthly for key in keys):
        return None
    return sum((monthly[key] for key in keys), Decimal("0"))


def complete_series(monthly: dict[tuple[int, int], Decimal], months: int, end_month: int) -> list[tuple[int, Decimal]]:
    first_year = min(year for year, _ in monthly)
    last_year = max(year for year, _ in monthly)
    rows: list[tuple[int, Decimal]] = []
    for end_year in range(first_year, last_year + 1):
        total = period_total(monthly, end_year, months, end_month)
        if total is not None:
            rows.append((end_year, total))
    return rows


def reference(monthly: dict[tuple[int, int], Decimal], selected_months: list[int]) -> Decimal:
    total = Decimal("0")
    for month in selected_months:
        values = [monthly[(year, month)] for year in range(1991, 2021)]
        if len(values) != 30:
            raise ValueError(f"Reference month {month} is incomplete")
        total += sum(values, Decimal("0")) / Decimal(30)
    return total


def linear_fit(rows: list[tuple[int, Decimal]]) -> tuple[Decimal, Decimal]:
    n = Decimal(len(rows))
    xs = [Decimal(year - 2000) for year, _ in rows]
    ys = [value for _, value in rows]
    x_mean = sum(xs, Decimal("0")) / n
    y_mean = sum(ys, Decimal("0")) / n
    numerator = sum(((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)), Decimal("0"))
    denominator = sum(((x - x_mean) ** 2 for x in xs), Decimal("0"))
    slope = numerator / denominator
    intercept = y_mean - slope * x_mean
    return intercept, slope


def close(actual: float, expected: Decimal, tolerance: Decimal = Decimal("0.000001")) -> bool:
    return abs(Decimal(str(actual)) - expected) <= tolerance


def run(source: Path, manifest: Path, summary_path: Path) -> dict[str, object]:
    failures: list[str] = []
    monthly, annual, last_updated = parse_fixed_width(source)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != manifest_data.get("sha256"):
        failures.append("source SHA-256 does not match provenance manifest")
    if summary.get("source_sha256") != digest:
        failures.append("summary source SHA-256 mismatch")
    if summary.get("source_last_updated") != last_updated:
        failures.append("summary Last updated mismatch")

    complete = complete_series(monthly, 12, 7)
    partials = complete_series(monthly, 11, 6)
    complete_reference = reference(monthly, list(range(1, 13)))
    partial_reference = reference(monthly, [8, 9, 10, 11, 12, 1, 2, 3, 4, 5, 6])
    latest_year, latest_total = complete[-1]
    partial_year, partial_total = partials[-1]
    partial_rank = 1 + sum(1 for _, value in partials if value > partial_total)
    wettest_year, wettest_total = max(complete, key=lambda item: item[1])
    driest_year, driest_total = min(complete, key=lambda item: item[1])

    if summary.get("complete_period_count") != len(complete):
        failures.append("complete-period count mismatch")
    if summary["latest_complete_period"]["end_year"] != latest_year:
        failures.append("latest complete end year mismatch")
    if not close(summary["latest_complete_period"]["rainfall_total_mm"], latest_total):
        failures.append("latest complete total mismatch")
    if not close(summary["current_incomplete_period"]["rainfall_total_mm"], partial_total):
        failures.append("current partial total mismatch")
    if summary["current_incomplete_period"]["wetness_rank"] != partial_rank:
        failures.append("current partial rank mismatch")
    if not close(summary["reference_1991_2020_august_july_mm"], complete_reference):
        failures.append("August-to-July reference mismatch")
    if not close(summary["reference_1991_2020_august_june_mm"], partial_reference):
        failures.append("August-to-June reference mismatch")
    if summary["wettest_complete_periods"][0]["rainfall_total_mm"] != float(wettest_total):
        failures.append("wettest period mismatch")
    if summary["driest_complete_periods"][0]["rainfall_total_mm"] != float(driest_total):
        failures.append("driest period mismatch")

    full_intercept, full_slope = linear_fit(complete)
    modern_rows = [(year, value) for year, value in complete if year >= 1970]
    modern_intercept, modern_slope = linear_fit(modern_rows)
    if not close(summary["trends"]["full_record"]["slope_mm_per_year"], full_slope):
        failures.append("full-record slope mismatch")
    if not close(summary["trends"]["modern_1970_onward"]["slope_mm_per_year"], modern_slope):
        failures.append("modern slope mismatch")

    milestones: dict[str, str] = {}
    for year in (2050, 2100):
        prediction = modern_intercept + modern_slope * Decimal(year - 2000)
        milestones[str(year)] = str(prediction)
        if not close(summary["statistical_projection"]["milestones"][str(year)]["primary_projection_mm"], prediction):
            failures.append(f"primary {year} projection mismatch")

    reconciliation_differences: list[Decimal] = []
    for year, official in annual.items():
        months = [monthly.get((year, month)) for month in range(1, 13)]
        if all(value is not None for value in months):
            reconstructed = sum((value for value in months if value is not None), Decimal("0"))
            reconciliation_differences.append(reconstructed - official)
    max_reconciliation = max(abs(value) for value in reconciliation_differences)
    if not close(summary["annual_reconciliation"]["max_abs_difference_mm"], max_reconciliation):
        failures.append("annual reconciliation mismatch")

    result = {
        "verification_status": "pass" if not failures else "fail",
        "failures": failures,
        "implementation": "independent Python standard library and Decimal",
        "source_sha256": digest,
        "source_last_updated": last_updated,
        "first_published_month": f"{min(monthly)[0]:04d}-{min(monthly)[1]:02d}",
        "last_published_month": f"{max(monthly)[0]:04d}-{max(monthly)[1]:02d}",
        "complete_august_to_july_periods": len(complete),
        "latest_complete_end_year": latest_year,
        "latest_complete_total_mm": str(latest_total),
        "current_august_to_june_end_year": partial_year,
        "current_august_to_june_total_mm": str(partial_total),
        "current_august_to_june_wetness_rank": partial_rank,
        "reference_1991_2020_august_july_mm": str(complete_reference),
        "reference_1991_2020_august_june_mm": str(partial_reference),
        "wettest_complete_end_year": wettest_year,
        "wettest_complete_total_mm": str(wettest_total),
        "driest_complete_end_year": driest_year,
        "driest_complete_total_mm": str(driest_total),
        "verified_full_record_slope_mm_per_decade": str(full_slope * Decimal(10)),
        "verified_modern_slope_mm_per_decade": str(modern_slope * Decimal(10)),
        "verified_primary_milestones_mm": milestones,
        "annual_reconciliation_max_abs_difference_mm": str(max_reconciliation),
    }
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    (DERIVED_DIR / "independent_verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit("; ".join(failures))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--summary", type=Path, default=DERIVED_DIR / "summary.json")
    args = parser.parse_args()
    source = args.source or discover_source()
    manifest = args.manifest or source.with_suffix(".provenance.json")
    print(json.dumps(run(source, manifest, args.summary), indent=2))


if __name__ == "__main__":
    main()
