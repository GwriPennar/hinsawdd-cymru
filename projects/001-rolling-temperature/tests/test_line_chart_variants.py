import json
from pathlib import Path
import sys

import matplotlib.image as mpimg
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from line_chart_variants import run, update_readmes  # noqa: E402


def _fixture() -> pd.DataFrame:
    starts = list(range(1884, 2026))
    ends = [year + 1 for year in starts]
    values = [7.2 + index * 0.022 for index in range(len(starts))]
    statuses = ["published-inputs"] * len(starts)
    statuses[-1] = "provisional-scenario"
    return pd.DataFrame(
        {
            "period": [f"{start}-08 to {end}-07" for start, end in zip(starts, ends)],
            "start_date": [f"{year}-08-01" for year in starts],
            "end_date": [f"{year}-07-31" for year in ends],
            "end_year": ends,
            "mean_temperature_c": values,
            "days": [365] * len(starts),
            "status": statuses,
            "rank_warmest": list(range(len(starts), 0, -1)),
        }
    )


def _summary() -> dict[str, object]:
    data = _fixture()
    return {
        "july_2026_value_used_c": 18.0,
        "source_last_updated": "01-Jul-2026 11:33",
        "derived_reference_1991_2020_c": 9.25,
        "previous_august_to_july_record": {
            "period": "2024-08 to 2025-07",
            "mean_temperature_c": float(data.iloc[-2]["mean_temperature_c"]),
        },
    }


def test_variants_generate_exact_dimensions_and_text(tmp_path: Path) -> None:
    source = tmp_path / "periods.csv"
    summary = tmp_path / "summary.json"
    standard = tmp_path / "standard"
    dark = tmp_path / "dark"
    output_csv = tmp_path / "chart.csv"
    _fixture().to_csv(source, index=False)
    summary.write_text(json.dumps(_summary()), encoding="utf-8")

    outputs = run(source, summary, standard, dark, output_csv)

    assert mpimg.imread(outputs.standard_png).shape[:2] == (900, 1600)
    assert mpimg.imread(outputs.dark_png).shape[:2] == (1080, 1080)
    standard_svg = outputs.standard_svg.read_text(encoding="utf-8")
    dark_svg = outputs.dark_svg.read_text(encoding="utf-8")
    assert "WALES AUGUST–JULY MEAN TEMPERATURE" in standard_svg
    assert "not a published Met Office value" in standard_svg
    assert "WALES: AUGUST–JULY" in dark_svg
    assert "2025–26 is the warmest equivalent period" in dark_svg
    assert "July 2026 remains provisional" in dark_svg
    data = pd.read_csv(outputs.data_csv)
    assert data.iloc[0]["period"] == "1884-08 to 1885-07"
    assert data.iloc[-1]["period"] == "2025-08 to 2026-07"


def test_readme_updates_are_idempotent(tmp_path: Path) -> None:
    root = tmp_path / "README.md"
    project = tmp_path / "project.md"
    root.write_text(
        "# Hinsawdd Cymru\n\n## Repository structure\n\n"
        "python projects/001-rolling-temperature/analysis.py\npytest\n",
        encoding="utf-8",
    )
    project.write_text(
        "# Project\n\n## Historical trend since records began\n\n"
        "python projects/001-rolling-temperature/august_to_july_stripes.py\npytest\n\n"
        "`analysis.py` performs the scientific calculation and produces the original full-width report figure. The presentation modules read validated derived outputs without introducing a second scientific method: `social_chart.py` produces the square dark chart, `warming_stripes.py` retains the calendar-year stripes and bars, and `august_to_july_stripes.py` produces the additional complete August-to-July stripes and bars documented in [`WARMING_STRIPES.md`](WARMING_STRIPES.md).\n\n"
        "- [`august_to_july_stripes.py`](august_to_july_stripes.py), additional August-to-July stripes and temperature bars\n"
        "- [`WARMING_STRIPES.md`](WARMING_STRIPES.md), full-width previews and interpretation for both annual boundaries\n\n"
        "- [`data/derived/wales_august_to_july_warming_stripes.csv`](data/derived/wales_august_to_july_warming_stripes.csv), August-to-July reference, anomalies and published/provisional status used by the new graphics\n"
        "- [`data/derived/independent_verification.json`](data/derived/independent_verification.json)\n\n"
        "Calendar-year and August-to-July warming stripes and temperature bars:\n",
        encoding="utf-8",
    )

    update_readmes(root, project)
    first_root = root.read_text(encoding="utf-8")
    first_project = project.read_text(encoding="utf-8")
    update_readmes(root, project)

    assert root.read_text(encoding="utf-8") == first_root
    assert project.read_text(encoding="utf-8") == first_project
    assert "wales_august_to_july_mean_temperature_line_chart_square_dark.png" in first_root
    assert "Standard light view" in first_project
    assert "line_chart_variants.py --update-readmes" in first_project


def test_retained_result_remains_unchanged() -> None:
    outputs = run()
    data = pd.read_csv(outputs.data_csv)
    assert data.iloc[-1]["mean_temperature_c"] == 10.626849
    assert data.iloc[-1]["status"] == "provisional-scenario"
    assert data.iloc[-1]["reference_mean_c"] == 9.418356
