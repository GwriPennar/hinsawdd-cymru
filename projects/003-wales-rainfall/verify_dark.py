"""Independent standard-library checks for Project 003 dark outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec = 40
PROJECT_DIR = Path(__file__).resolve().parent
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
SEASONS = ["win", "spr", "sum", "aut"]
FIELDS = (
    [("year", 0, 4)]
    + [(name, 5 + 7 * i, 12 + 7 * i) for i, name in enumerate(MONTHS)]
    + [(name, 89 + 8 * i, 97 + 8 * i) for i, name in enumerate(SEASONS)]
    + [("ann", 121, 129)]
)
STEMS = (
    "wales_august_to_july_rainfall_history_dark",
    "wales_july_rainfall_history_dark",
    "wales_august_to_july_rainfall_dryness_dark",
    "wales_august_to_july_raindays_history_dark",
    "wales_rainfall_statistical_projection_dark",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_source(path: Path, description: str) -> tuple[dict[tuple[int, int], Decimal], str]:
    text = path.read_text(encoding="utf-8")
    if description not in text:
        raise ValueError(f"Unexpected source content: {path}")
    updated = re.search(r"^Last updated\s+(.+)$", text, re.MULTILINE)
    if not updated:
        raise ValueError("Missing Last updated field")
    lines = text.splitlines()
    header = next(i for i, line in enumerate(lines) if line.lstrip().startswith("year"))
    expected = ["year", *MONTHS, *SEASONS, "ann"]
    if re.findall(r"\S+", lines[header].lower()) != expected:
        raise ValueError("Unexpected source columns")
    monthly: dict[tuple[int, int], Decimal] = {}
    for line in lines[header + 1 :]:
        if not re.match(r"^\d{4}\b", line):
            continue
        padded = line.ljust(129)
        row = {name: padded[start:end].strip() for name, start, end in FIELDS}
        year = int(row["year"])
        for month, name in enumerate(MONTHS, start=1):
            if row[name] not in {"", "---"}:
                monthly[(year, month)] = Decimal(row[name])
    return monthly, updated.group(1).strip()


def period_series(monthly: dict[tuple[int, int], Decimal]) -> list[tuple[int, Decimal]]:
    first = min(year for year, _ in monthly)
    last = max(year for year, _ in monthly)
    rows: list[tuple[int, Decimal]] = []
    for end_year in range(first, last + 1):
        keys = []
        for offset in range(11, -1, -1):
            index = end_year * 12 + 6 - offset
            year, zero_month = divmod(index, 12)
            keys.append((year, zero_month + 1))
        if all(key in monthly for key in keys):
            rows.append((end_year, sum((monthly[key] for key in keys), Decimal(0))))
    return rows


def reference(monthly: dict[tuple[int, int], Decimal], months: range | tuple[int, ...]) -> Decimal:
    total = Decimal(0)
    for month in months:
        total += sum((monthly[(year, month)] for year in range(1991, 2021)), Decimal(0)) / Decimal(30)
    return total


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError(f"Not a PNG: {path}")
    return struct.unpack(">II", data[16:24])


def close(actual: object, expected: Decimal, tolerance: Decimal = Decimal("0.000001")) -> bool:
    return abs(Decimal(str(actual)) - expected) <= tolerance


def check_manifest(source: Path, manifest: Path) -> None:
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if data.get("sha256") != sha256(source):
        raise ValueError(f"SHA-256 mismatch: {source.name}")
    if data.get("exact_upstream_bytes") is not True:
        raise ValueError(f"Manifest does not assert exact upstream bytes: {source.name}")


def run(args: argparse.Namespace) -> dict[str, object]:
    check_manifest(args.rainfall_source, args.rainfall_manifest)
    check_manifest(args.raindays_source, args.raindays_manifest)
    rainfall, rainfall_updated = parse_source(
        args.rainfall_source,
        "Monthly, seasonal and annual total precipitation amount for Wales",
    )
    raindays, raindays_updated = parse_source(
        args.raindays_source,
        "Monthly, seasonal and annual number of days in the month with precipitation amount >= 1mm for Wales",
    )
    rain_periods = period_series(rainfall)
    day_periods = period_series(raindays)
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    latest_year, latest_rain = rain_periods[-1]
    latest_day_year, latest_days = day_periods[-1]
    july_values = sorted((value, year) for (year, month), value in rainfall.items() if month == 7)
    july_2026 = rainfall[(2026, 7)]
    july_rank = 1 + sum(value < july_2026 for value, _ in july_values)
    refs = summary["reference_1991_2020"]
    latest = summary["latest_complete_august_to_july"]
    july = summary["july_2026"]
    checks = {
        "rainfall update": summary["source_last_updated"]["rainfall"] == rainfall_updated,
        "rain-days update": summary["source_last_updated"]["raindays1mm"] == raindays_updated,
        "latest shared year": latest_year == latest_day_year,
        "latest rainfall": close(latest["rainfall_total_mm"], latest_rain),
        "latest rain days": close(latest["rain_days_ge_1mm"], latest_days),
        "rainfall reference": close(refs["august_to_july_rainfall_mm"], reference(rainfall, range(1, 13))),
        "July reference": close(refs["july_rainfall_mm"], reference(rainfall, (7,))),
        "rain-day reference": close(refs["august_to_july_raindays_ge_1mm"], reference(raindays, range(1, 13))),
        "July 2026 value": close(july["rainfall_mm"], july_2026),
        "July 2026 rank": int(july["dryness_rank"]) == july_rank,
        "July comparison count": int(july["comparison_years"]) == len(july_values),
    }
    failures = [name for name, passed in checks.items() if not passed]
    for stem in STEMS:
        wide_png = args.figures_dir / f"{stem}.png"
        square_png = args.figures_dir / f"{stem}_square.png"
        wide_svg = args.figures_dir / f"{stem}.svg"
        square_svg = args.figures_dir / f"{stem}_square.svg"
        for path in (wide_png, square_png, wide_svg, square_svg):
            if not path.exists():
                failures.append(f"missing {path.name}")
        if wide_png.exists() and png_size(wide_png) != (1600, 900):
            failures.append(f"wrong dimensions {wide_png.name}")
        if square_png.exists() and png_size(square_png) != (1080, 1080):
            failures.append(f"wrong dimensions {square_png.name}")
        for svg in (wide_svg, square_svg):
            if svg.exists() and "#080c16" not in svg.read_text(encoding="utf-8").lower():
                failures.append(f"dark background missing {svg.name}")
    result = {
        "verification_status": "pass" if not failures else "fail",
        "failures": failures,
        "rainfall_source_sha256": sha256(args.rainfall_source),
        "raindays_source_sha256": sha256(args.raindays_source),
        "latest_complete_end_year": latest_year,
        "latest_complete_rainfall_mm": str(latest_rain),
        "latest_complete_raindays_ge_1mm": str(latest_days),
        "july_2026_rainfall_mm": str(july_2026),
        "july_2026_dryness_rank": july_rank,
        "verified_figure_pairs": len(STEMS),
    }
    output = PROJECT_DIR / "data/derived/independent_dark_verification.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit("; ".join(failures))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rainfall-source", type=Path, required=True)
    parser.add_argument("--rainfall-manifest", type=Path, required=True)
    parser.add_argument("--raindays-source", type=Path, required=True)
    parser.add_argument("--raindays-manifest", type=Path, required=True)
    parser.add_argument("--summary", type=Path, default=PROJECT_DIR / "data/derived/dark_chart_summary.json")
    parser.add_argument("--figures-dir", type=Path, default=PROJECT_DIR / "figures")
    print(json.dumps(run(parser.parse_args()), indent=2))


if __name__ == "__main__":
    main()
