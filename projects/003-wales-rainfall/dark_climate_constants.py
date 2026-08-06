"""Shared constants and data containers for Project 003."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

MONTH_COLUMNS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
MONTH_NUMBERS = {name: index for index, name in enumerate(MONTH_COLUMNS, start=1)}
SEASON_COLUMNS = ["win", "spr", "sum", "aut"]
PROJECT_DIR = Path(__file__).resolve().parent
README_PATH = PROJECT_DIR / "README.md"
RESULT_START = "<!-- BEGIN GENERATED RESULT -->"
RESULT_END = "<!-- END GENERATED RESULT -->"
FIELD_SPECS = (
    [("year", 0, 4)]
    + [(name, 5 + 7 * index, 12 + 7 * index) for index, name in enumerate(MONTH_COLUMNS)]
    + [(name, 89 + 8 * index, 97 + 8 * index) for index, name in enumerate(SEASON_COLUMNS)]
    + [("ann", 121, 129)]
)

DARK_BG = "#080c16"
PANEL_BG = "#0f172a"
TEXT = "#f8fafc"
MUTED = "#94a3b8"
GRID = "#334155"
CYAN = "#22d3ee"
BLUE = "#60a5fa"
WET = "#38bdf8"
DRY = "#f59e0b"
DRY_STRONG = "#fb7185"
WHITE = "#ffffff"


@dataclass(frozen=True)
class SourceBundle:
    metric: str
    monthly: pd.DataFrame
    annual: pd.DataFrame
    source_last_updated: str


@dataclass(frozen=True)
class LinearFit:
    intercept_at_2000: float
    slope_per_year: float
    r_squared: float
    residual_standard_error: float
    observation_count: int
    first_year: int
    last_year: int

    @property
    def slope_per_decade(self) -> float:
        return self.slope_per_year * 10.0

    def predict(self, years: np.ndarray | pd.Series | list[int]) -> np.ndarray:
        values = np.asarray(years, dtype=float)
        return self.intercept_at_2000 + self.slope_per_year * (values - 2000.0)

    def to_dict(self) -> dict[str, float | int]:
        result = asdict(self)
        result["slope_per_decade"] = self.slope_per_decade
        return result
