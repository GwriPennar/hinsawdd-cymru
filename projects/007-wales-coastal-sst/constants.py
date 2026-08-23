"""Shared paths and defaults for Project 007 Stage A."""
from __future__ import annotations

from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
DERIVED_DIR = PROJECT_DIR / "data" / "derived"
FIGURES_DIR = PROJECT_DIR / "figures"

LON_MIN = -6.5
LON_MAX = -2.6
LAT_MIN = 51.2
LAT_MAX = 53.6

CLIM_START = 1991
CLIM_END = 2020
SERIES_CHART_YEARS = 20

# Met Office HadISST1 monthly SST (open HadOBS download).
HADISST_URL = "https://www.metoffice.gov.uk/hadobs/hadisst/data/HadISST_sst.nc.gz"
HADISST_TIME_ORIGIN = "1870-01-01"

ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"

DARK_BG = "#080c16"
PANEL_BG = "#0f172a"
TEXT = "#f8fafc"
MUTED = "#94a3b8"
GRID = "#334155"
CYAN = "#22d3ee"
BLUE = "#60a5fa"
WARM = "#f59e0b"
HOT = "#fb7185"
COOL = "#38bdf8"
