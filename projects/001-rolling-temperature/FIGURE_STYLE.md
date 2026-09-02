# Project 001 figure style guide

Project supplement to the repository-wide [`VISUAL_STYLE.md`](../../VISUAL_STYLE.md). Shared renderers live in [`trend_charts.py`](trend_charts.py); colours and legend strings in [`figure_style.py`](figure_style.py).

Golden reference for August–July layout: `~/Documents/hinsawdd-cymru-snapshots/001-pre-monthly-monitor-3188e14` (commit `3188e14`). Rolling charts should match the same colour families and legend placement.

## Live rolling monitor figures

| Figure | Generator | Dimensions | Key visual rules |
|---|---|---|---|
| Light history | `monthly_monitor.py` → `trend_charts.render_light_trend()` | 12×6.5 @ 220 DPI | Blue/orange/grey; 3-line rolling legend upper-left |
| Dark social square | `monthly_monitor.py` → `trend_charts.render_social_dark()` | 1080×1080 | Red/cyan/grey; headline block top-left |
| Standard line chart | `rolling_line_chart.py` | 1600×900 | Gaussian trend; previous high from prior published window |
| Dark square line | `rolling_line_chart.py` | 1080×1080 | Dark bg `#040914`; previous-high label must not use current window value |

## Archived August–July figures

| Figure | Generator | Notes |
|---|---|---|
| Main trend (light) | `analysis.make_figure()` | Archive / comparison only; not published to live `figures/` |
| Square dark social | `social_chart.py` | Frozen in `archive/august-to-july-2025-26/` |
| Line variants | `line_chart_variants.py` | Archive copies only |
| Stripes / bars | `august_to_july_stripes.py` | Optional compatibility outputs |

## Legend strings

**Rolling monitor (live):**

1. `Individual rolling 12-month windows`
2. `Trailing 10-window average`
3. `Derived 1991–2020 reference`

**August–July (archive):**

1. `Individual August-to-July periods`
2. `Trailing 10-year average`
3. `Derived 1991–2020 reference`

## Monthly refresh checklist

1. `python projects/001-rolling-temperature/refresh.py --fetch` (or `refresh.py` if source already current).
2. Confirm `runs/YYYY-MM/` snapshot created and `runs/index.json` updated.
3. Verify rolling SVG legend strings (`tests/test_figure_style.py`, `tests/test_monthly_monitor.py`).
4. Compare PNG visually against golden snapshot worktree (colours/layout, not series length).
5. Run `pytest -q projects/001-rolling-temperature/tests`.

## Run snapshots

Each refresh freezes outputs under `runs/YYYY-MM/` (`RUN.md`, `manifest.json`, `data/`, `figures/`). Live `figures/` keeps stable public URLs for the latest refresh only.
