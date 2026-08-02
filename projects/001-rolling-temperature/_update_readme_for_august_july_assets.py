"""One-time branch migration for Project 001 README output documentation."""
from __future__ import annotations

from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
README = PROJECT_DIR / "README.md"
SCRIPT = Path(__file__).resolve()


def replace_once(text: str, old: str, new: str) -> str:
    """Replace one known block, failing if repository context has drifted."""

    if text.count(old) != 1:
        raise RuntimeError(
            f"Expected one README match, found {text.count(old)}: {old[:80]!r}"
        )
    return text.replace(old, new, 1)


def main() -> None:
    """Patch the Project 001 README once, then self-delete."""

    text = README.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "python projects/001-rolling-temperature/social_chart.py\npytest",
        "python projects/001-rolling-temperature/social_chart.py\n"
        "python projects/001-rolling-temperature/warming_stripes.py\n"
        "python projects/001-rolling-temperature/august_to_july_stripes.py\n"
        "pytest",
    )
    text = replace_once(
        text,
        "`analysis.py` performs the calculation and produces the original full-width report figure. `social_chart.py` is a presentation-only extension: it reads the validated derived CSV and `summary.json`, then produces the square dark Seaborn version without recalculating the result.",
        "`analysis.py` performs the scientific calculation and produces the original full-width report figure. The presentation modules read validated derived outputs without introducing a second scientific method: `social_chart.py` produces the square dark chart, `warming_stripes.py` retains the calendar-year stripes and bars, and `august_to_july_stripes.py` produces the additional complete August-to-July stripes and bars documented in [`WARMING_STRIPES.md`](WARMING_STRIPES.md).",
    )
    text = replace_once(
        text,
        "- [`social_chart.py`](social_chart.py), square dark social figure rendered from the validated derived outputs\n- [`verify.py`](verify.py), independent standard-library and `Decimal` verification",
        "- [`social_chart.py`](social_chart.py), square dark social figure rendered from the validated derived outputs\n"
        "- [`warming_stripes.py`](warming_stripes.py), retained calendar-year stripes and temperature bars\n"
        "- [`august_to_july_stripes.py`](august_to_july_stripes.py), additional August-to-July stripes and temperature bars\n"
        "- [`WARMING_STRIPES.md`](WARMING_STRIPES.md), full-width previews and interpretation for both annual boundaries\n"
        "- [`verify.py`](verify.py), independent standard-library and `Decimal` verification",
    )
    text = replace_once(
        text,
        "- [`data/derived/annual_reconciliation.csv`](data/derived/annual_reconciliation.csv), reconstructed and official annual values\n- [`data/derived/independent_verification.json`](data/derived/independent_verification.json), second-implementation verification result",
        "- [`data/derived/annual_reconciliation.csv`](data/derived/annual_reconciliation.csv), reconstructed and official annual values\n"
        "- [`data/derived/wales_calendar_year_warming_stripes.csv`](data/derived/wales_calendar_year_warming_stripes.csv), calendar-year reference and anomalies used by the retained calendar graphics\n"
        "- [`data/derived/wales_august_to_july_warming_stripes.csv`](data/derived/wales_august_to_july_warming_stripes.csv), August-to-July reference, anomalies and published/provisional status used by the new graphics\n"
        "- [`data/derived/independent_verification.json`](data/derived/independent_verification.json), second-implementation verification result",
    )
    text = replace_once(
        text,
        "- [`figures/wales_august_to_july_mean_temperature_square_dark.png`](figures/wales_august_to_july_mean_temperature_square_dark.png), 1080 × 1080 raster version\n\n## Technical appendices",
        "- [`figures/wales_august_to_july_mean_temperature_square_dark.png`](figures/wales_august_to_july_mean_temperature_square_dark.png), 1080 × 1080 raster version\n\n"
        "Calendar-year and August-to-July warming stripes and temperature bars:\n\n"
        "- [`WARMING_STRIPES.md`](WARMING_STRIPES.md), full-width clickable previews of all retained PNG assets and links to their SVG counterparts\n"
        "- `figures/wales_august_to_july_warming_stripes.{png,svg}`\n"
        "- `figures/wales_august_to_july_warming_stripes_explained.{png,svg}`\n"
        "- `figures/wales_august_to_july_temperature_bars.{png,svg}`\n"
        "- `figures/wales_august_to_july_temperature_bars_explained.{png,svg}`\n\n"
        "## Technical appendices",
    )
    README.write_text(text, encoding="utf-8")
    SCRIPT.unlink()


if __name__ == "__main__":
    main()
