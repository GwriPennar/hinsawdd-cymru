"""Shared colours, dimensions and legend labels for Project 001 figures."""

from __future__ import annotations

# Light trend chart (analysis.py make_figure)
LIGHT_TREND_FIGSIZE = (12, 6.5)
LIGHT_TREND_DPI = 220
LIGHT_PERIOD_COLOUR = "#1f77b4"
LIGHT_AVERAGE_COLOUR = "#ff7f0e"
LIGHT_REFERENCE_COLOUR = "#89919c"

# Dark social chart (social_chart.py)
SOCIAL_BACKGROUND = "#090b10"
SOCIAL_FOREGROUND = "#f5f7fa"
SOCIAL_MUTED = "#aab2bd"
SOCIAL_GRID = "#303641"
SOCIAL_PERIOD_COLOUR = "#ff4d5a"
SOCIAL_AVERAGE_COLOUR = "#45e0e5"
SOCIAL_PREVIOUS_HIGH = "#ffd166"
SOCIAL_REFERENCE_COLOUR = "#89919c"
SOCIAL_FIGSIZE_INCHES = (10.8, 10.8)
SOCIAL_DPI = 100

# Dark line chart (line_chart_variants.py render_dark)
DARK_LINE_BACKGROUND = "#040914"
DARK_LINE_FOREGROUND = "#e5e7eb"
DARK_LINE_MUTED = "#a9b1bf"
DARK_LINE_GRID = "#334155"
DARK_LINE_PERIOD_COLOUR = "#cc3a53"
DARK_LINE_TREND_COLOUR = "#32d3e2"
DARK_LINE_REFERENCE_COLOUR = "#94a3b8"
DARK_LINE_PREVIOUS_HIGH = "#f2c94c"
DARK_LINE_LATEST = "#ff5a67"
DARK_LINE_FRAME = "#2b3445"

# Standard line chart (line_chart_variants.py render_standard)
STANDARD_WIDTH_PX = 1600
STANDARD_HEIGHT_PX = 900
SQUARE_PX = 1080
LINE_CHART_DPI = 100

# August-to-July legend labels (canonical three-line legend)
LABEL_INDIVIDUAL_PERIODS = "Individual August-to-July periods"
LABEL_TRAILING_AVERAGE = "Trailing 10-year average"
LABEL_REFERENCE_1991_2020 = "Derived 1991–2020 reference"

# Rolling 12-month monitor (monthly_monitor.py on feature branch)
LABEL_ROLLING_WINDOWS = "Individual rolling 12-month windows"
LABEL_ROLLING_AVERAGE = "Trailing 10-window average"
