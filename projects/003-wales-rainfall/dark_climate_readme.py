"""Update the generated Project 003 README result block."""

from __future__ import annotations

import re
from pathlib import Path

from dark_climate_constants import RESULT_END, RESULT_START

README_PATH = Path(__file__).resolve().parent / "README.md"

def update_readme(summary: dict[str, object]) -> None:
    """Replace the generated headline block with the current dark-suite findings."""

    text = README_PATH.read_text(encoding="utf-8")
    latest = summary["latest_complete_august_to_july"]
    july = summary["july_2026"]
    refs = summary["reference_1991_2020"]
    fits = summary["statistical_projection"]["primary_fit"]
    milestones = summary["statistical_projection"]["milestones"]
    coverage = summary["source_coverage"]
    driest = summary["driest_complete_august_to_july"]
    wettest = summary["wettest_complete_august_to_july"]
    block = f"""{RESULT_START}
## Headline results

| Measure | Result |
|---|---:|
| Official rainfall coverage | **{coverage['rainfall_first_month']} to {coverage['rainfall_last_month']}** |
| Complete August-to-July periods | **{summary['complete_august_to_july_period_count']}** |
| 1991–2020 August-to-July reference | **{refs['august_to_july_rainfall_mm']:.1f} mm** |
| Latest complete period | **{latest['period']}** |
| Latest complete rainfall | **{latest['rainfall_total_mm']:.1f} mm**, {latest['percentage_of_1991_2020']:.1f}% of reference |
| July 2026 rainfall | **{july['rainfall_mm']:.1f} mm**, {july['percentage_of_1991_2020']:.1f}% of the July reference |
| July 2026 dryness rank | **{july['dryness_rank']} of {july['comparison_years']} Julys** |
| Latest rain days ≥1 mm | **{latest['rain_days_ge_1mm']:.1f} days**, {latest['rain_days_percentage_of_1991_2020']:.1f}% of reference |
| Driest complete period | **{driest['period']}**, {driest['rainfall_total_mm']:.1f} mm |
| Wettest complete period | **{wettest['period']}**, {wettest['rainfall_total_mm']:.1f} mm |
| Modern rainfall trend, 1970 onward | **{fits['slope_per_decade']:+.1f} mm per decade** |
| Illustrative 2050 continuation | **{milestones['2050']['primary_projection_mm']:.0f} mm** |
| Illustrative 2100 continuation | **{milestones['2100']['primary_projection_mm']:.0f} mm** |

July 2026 was the driest July in the Wales series beginning in 1836. That does **not** mean the complete August 2025–July 2026 period was exceptionally dry: its total was slightly above the 1991–2020 August-to-July reference. Monthly dryness, annual rainfall and formal drought status are therefore kept separate.

The continuation values are a transparent statistical baseline, not a physical climate forecast or an official Met Office, UKCP or UKCI projection.
{RESULT_END}"""
    pattern = re.compile(re.escape(RESULT_START) + r".*?" + re.escape(RESULT_END), re.DOTALL)
    if not pattern.search(text):
        raise ValueError("README generated-result markers missing")
    README_PATH.write_text(pattern.sub(block, text), encoding="utf-8")
