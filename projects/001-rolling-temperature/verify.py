"""Independent standard-library verification for Project 001.

This module deliberately does not import analysis.py, pandas, NumPy or Seaborn.
"""

from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import math
import re
from dataclasses import dataclass
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec = 28
MONTHS = "jan feb mar apr may jun jul aug sep oct nov dec".split()
LAST_UPDATED_RE = re.compile(r"^(?:Last updated|Source last updated:)\s*(.+)$", re.MULTILINE)


@dataclass(frozen=True)
class ParsedSource:
    monthly: dict[tuple[int, int], Decimal]
    official_annual: dict[int, Decimal]
    last_updated: str | None


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_source(path: Path) -> ParsedSource:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    header_index = next((i for i, line in enumerate(lines) if line.strip().lower().startswith("year")), None)
    if header_index is None:
        raise ValueError("Missing source header")
    header_line = lines[header_index]
    matches = list(re.finditer(r"\S+", header_line))
    header = [match.group(0) for match in matches]
    missing = {"year", *MONTHS}.difference(header)
    if missing:
        raise ValueError(f"Missing source columns: {sorted(missing)}")
    ends = [match.end() for match in matches]
    spans = [(0 if index == 0 else ends[index - 1], ends[index]) for index in range(len(ends))]

    def fixed_fields(raw: str) -> dict[str, str]:
        # The official text table right-aligns values to the end of each header token.
        return {
            name: raw[start:end].strip()
            for name, (start, end) in zip(header, spans, strict=True)
        }

    monthly: dict[tuple[int, int], Decimal] = {}
    annual: dict[int, Decimal] = {}
    for raw in lines[header_index + 1 :]:
        fields = fixed_fields(raw)
        year_token = fields.get("year", "")
        if not year_token.lstrip("-").isdigit():
            continue
        year = int(year_token)
        for month, name in enumerate(MONTHS, 1):
            token = fields.get(name, "")
            if not token or token in {"---", "NaN"}:
                continue
            monthly[(year, month)] = Decimal(token)
        token = fields.get("ann", "")
        if token and token not in {"---", "NaN"}:
            annual[year] = Decimal(token)
    if not monthly:
        raise ValueError("No monthly values parsed")
    match = LAST_UPDATED_RE.search(text)
    return ParsedSource(monthly, annual, match.group(1).strip() if match else None)


def days_in_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def weighted_period_mean(monthly: dict[tuple[int, int], Decimal], months: list[tuple[int, int]]) -> Decimal:
    numerator = Decimal(0)
    denominator = 0
    for year, month in months:
        value = monthly[(year, month)]
        days = days_in_month(year, month)
        numerator += value * days
        denominator += days
    return numerator / Decimal(denominator)


def aug_to_jul_months(end_year: int) -> list[tuple[int, int]]:
    return [(end_year - 1, month) for month in range(8, 13)] + [(end_year, month) for month in range(1, 8)]


def annual_reconciliation(source: ParsedSource) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for year, official in sorted(source.official_annual.items()):
        months = [(year, month) for month in range(1, 13)]
        if not all(key in source.monthly for key in months):
            continue
        derived = weighted_period_mean(source.monthly, months)
        difference = derived - official
        rows.append({
            "year": year,
            "derived_from_rounded_months_c": float(derived),
            "official_annual_mean_c": float(official),
            "difference_c": float(difference),
            "absolute_difference_c": float(abs(difference)),
        })
    return rows


def verify(
    source_path: Path,
    *,
    july_2026_c: Decimal = Decimal("18.0"),
    manifest_path: Path | None = None,
    primary_summary_path: Path | None = None,
    require_annual: bool = False,
) -> dict[str, object]:
    source = parse_source(source_path)
    failures: list[str] = []

    if manifest_path is not None:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("sha256") != file_sha256(source_path):
            failures.append("source SHA-256 does not match provenance manifest")
        if manifest.get("exact_upstream_bytes") is not True:
            failures.append("provenance manifest does not mark the source as exact upstream bytes")

    first_month = min(source.monthly)
    last_month = max(source.monthly)
    cursor = first_month
    while cursor <= last_month:
        if cursor not in source.monthly:
            failures.append(f"missing monthly value: {cursor[0]}-{cursor[1]:02d}")
            break
        year, month = cursor
        cursor = (year + 1, 1) if month == 12 else (year, month + 1)

    monthly = dict(source.monthly)
    july_kind = "published" if (2026, 7) in monthly else "illustrative_scenario"
    monthly.setdefault((2026, 7), july_2026_c)

    complete_periods: list[tuple[int, Decimal]] = []
    for end_year in range(first_month[0] + 1, 2027):
        months = aug_to_jul_months(end_year)
        if all(key in monthly for key in months):
            complete_periods.append((end_year, weighted_period_mean(monthly, months)))
    current = next(value for year, value in complete_periods if year == 2026)
    historical = [(year, value) for year, value in complete_periods if year < 2026]
    previous_year, previous = max(historical, key=lambda item: item[1])
    rank = 1 + sum(value > current for _, value in complete_periods)

    known_months = [(2025, month) for month in range(8, 13)] + [(2026, month) for month in range(1, 7)]
    known_temperature_days = sum(source.monthly[key] * days_in_month(*key) for key in known_months)
    required_july = (previous * Decimal(365) - known_temperature_days) / Decimal(31)

    annual_rows = annual_reconciliation(source)
    if require_annual and not annual_rows:
        failures.append("official annual column is required but was not available")
    max_annual_difference = max((row["absolute_difference_c"] for row in annual_rows), default=None)
    if max_annual_difference is not None and max_annual_difference > 0.06:
        failures.append(f"annual reconciliation exceeded 0.06°C: {max_annual_difference:.6f}°C")

    result: dict[str, object] = {
        "verification_status": "pass" if not failures else "fail",
        "failures": failures,
        "source_path": str(source_path),
        "source_sha256": file_sha256(source_path),
        "source_last_updated": source.last_updated,
        "first_published_month": f"{first_month[0]:04d}-{first_month[1]:02d}",
        "last_published_month": f"{last_month[0]:04d}-{last_month[1]:02d}",
        "july_2026_value_c": float(monthly[(2026, 7)]),
        "july_2026_value_kind": july_kind,
        "period_mean_c": float(current),
        "rank_among_august_to_july_periods": rank,
        "previous_record": {
            "period": f"{previous_year - 1}-08 to {previous_year}-07",
            "mean_temperature_c": float(previous),
        },
        "july_2026_mean_needed_to_break_previous_record_c": float(required_july),
        "annual_reconciliation_years": len(annual_rows),
        "annual_reconciliation_max_abs_difference_c": max_annual_difference,
        "implementation": "independent Python standard library and Decimal",
    }

    if primary_summary_path is not None:
        primary = json.loads(primary_summary_path.read_text(encoding="utf-8"))
        comparisons = {
            "period_mean_central_c": float(current),
            "rank_among_august_to_july_periods": rank,
            "july_2026_mean_needed_to_break_previous_august_to_july_record_c": float(required_july),
        }
        for key, independent in comparisons.items():
            primary_value = primary[key]
            if isinstance(independent, float):
                if not math.isclose(float(primary_value), independent, rel_tol=0, abs_tol=1e-12):
                    failures.append(f"primary and independent results differ for {key}: {primary_value} vs {independent}")
            elif primary_value != independent:
                failures.append(f"primary and independent results differ for {key}: {primary_value} vs {independent}")
        result["primary_summary_comparison"] = "pass" if not any("primary and independent" in item for item in failures) else "fail"
        result["verification_status"] = "pass" if not failures else "fail"
        result["failures"] = failures

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--primary-summary", type=Path)
    parser.add_argument("--july-2026", type=Decimal, default=Decimal("18.0"))
    parser.add_argument("--require-annual", action="store_true")
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    result = verify(
        args.source,
        july_2026_c=args.july_2026,
        manifest_path=args.manifest,
        primary_summary_path=args.primary_summary,
        require_annual=args.require_annual,
    )
    rendered = json.dumps(result, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if result["verification_status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
