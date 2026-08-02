"""Independent standard-library verification for Project 002."""

from __future__ import annotations

import argparse
import csv
import json
from decimal import Decimal, getcontext
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
DERIVED_DIR = PROJECT_DIR / "data/derived"
OBSERVED_CSV = DERIVED_DIR / "observed_august_to_july_input.csv"
SUMMARY_JSON = DERIVED_DIR / "model_summary.json"
SOURCE_VERIFICATION = DERIVED_DIR / "source_verification_snapshot.json"
OUTPUT_JSON = DERIVED_DIR / "independent_verification.json"
YEAR_CENTRE = Decimal("2000")
TOLERANCE = Decimal("0.000002")

getcontext().prec = 40


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _published_rows(path: Path, start_year: int) -> list[tuple[Decimal, Decimal]]:
    rows: list[tuple[Decimal, Decimal]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            year = int(row["end_year"])
            if row["status"] == "published-inputs" and year >= start_year:
                rows.append(
                    (
                        Decimal(str(year)),
                        Decimal(row["temperature_anomaly_c"]),
                    )
                )
    return rows


def _ols(rows: list[tuple[Decimal, Decimal]]) -> tuple[Decimal, Decimal]:
    count = Decimal(len(rows))
    x_values = [year - YEAR_CENTRE for year, _ in rows]
    y_values = [value for _, value in rows]
    x_mean = sum(x_values) / count
    y_mean = sum(y_values) / count
    numerator = sum(
        (x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values)
    )
    denominator = sum((x - x_mean) ** 2 for x in x_values)
    slope = numerator / denominator
    intercept = y_mean - slope * x_mean
    return intercept, slope


def verify(
    observed_csv: Path = OBSERVED_CSV,
    summary_json: Path = SUMMARY_JSON,
    source_verification_json: Path = SOURCE_VERIFICATION,
    output_json: Path = OUTPUT_JSON,
) -> dict[str, object]:
    summary = _load_json(summary_json)
    source_verification = _load_json(source_verification_json)
    failures: list[str] = []

    if source_verification.get("verification_status") != "pass":
        failures.append("Project 001 verification snapshot is not pass")
    if source_verification.get("primary_summary_comparison") != "pass":
        failures.append("Project 001 primary-summary comparison is not pass")

    fit_start = int(summary["configuration"]["fit_start_end_year"])
    rows = _published_rows(observed_csv, fit_start)
    intercept, slope = _ols(rows)
    primary = summary["primary_fit"]
    expected_intercept = Decimal(str(primary["intercept_at_2000_c"]))
    expected_slope = Decimal(str(primary["slope_c_per_year"]))

    if abs(intercept - expected_intercept) > TOLERANCE:
        failures.append("Primary OLS intercept differs")
    if abs(slope - expected_slope) > TOLERANCE:
        failures.append("Primary OLS slope differs")

    reference = Decimal(str(summary["reference_mean_1991_2020_c"]))
    milestone_checks: dict[str, str] = {}
    for year in (
        2050,
        2100,
        int(summary["configuration"]["projection_end_year"]),
    ):
        predicted = reference + intercept + slope * (Decimal(year) - YEAR_CENTRE)
        expected = Decimal(
            str(summary["milestones"][str(year)]["primary_mean_temperature_c"])
        )
        difference = abs(predicted - expected)
        milestone_checks[str(year)] = str(predicted)
        if difference > TOLERANCE:
            failures.append(f"Primary milestone {year} differs")

    result: dict[str, object] = {
        "verification_status": "pass" if not failures else "fail",
        "failures": failures,
        "implementation": "independent Python standard library and Decimal",
        "published_training_observations": len(rows),
        "fit_start_end_year": fit_start,
        "verified_intercept_at_2000_c": str(intercept),
        "verified_slope_c_per_year": str(slope),
        "verified_slope_c_per_decade": str(slope * Decimal("10")),
        "verified_primary_milestones_c": milestone_checks,
        "source_snapshot_sha256": summary["source_snapshot_sha256"],
        "source_project_verification": source_verification.get(
            "verification_status"
        ),
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    if failures:
        raise SystemExit("; ".join(failures))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observed-csv", type=Path, default=OBSERVED_CSV)
    parser.add_argument("--summary-json", type=Path, default=SUMMARY_JSON)
    parser.add_argument(
        "--source-verification-json", type=Path, default=SOURCE_VERIFICATION
    )
    parser.add_argument("--output-json", type=Path, default=OUTPUT_JSON)
    args = parser.parse_args()
    print(
        json.dumps(
            verify(
                args.observed_csv,
                args.summary_json,
                args.source_verification_json,
                args.output_json,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
