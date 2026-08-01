from pathlib import Path
import sys

import matplotlib.image as mpimg
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from social_chart import make_square_dark_figure  # noqa: E402


def test_square_dark_social_chart_is_exactly_1080_square(tmp_path: Path) -> None:
    series = pd.DataFrame(
        {
            "end_year": list(range(2007, 2027)),
            "mean_temperature_c": [
                9.1,
                9.2,
                9.0,
                9.3,
                9.4,
                9.5,
                9.6,
                9.7,
                9.5,
                9.8,
                9.9,
                10.0,
                9.8,
                10.1,
                10.0,
                10.2,
                10.1,
                10.3,
                10.2,
                10.6,
            ],
        }
    )

    png_path, svg_path = make_square_dark_figure(
        series,
        tmp_path / "social",
        july_2026_c=18.0,
        status="provisional-scenario",
        reference_1991_2020_c=9.42,
    )

    image = mpimg.imread(png_path)
    assert image.shape[:2] == (1080, 1080)
    assert svg_path.exists()

    svg = svg_path.read_text(encoding="utf-8")
    assert "WALES: AUGUST–JULY MEAN TEMPERATURE" in svg
    assert "Trailing 10-year average" in svg
    assert "illustrative scenario" in svg
