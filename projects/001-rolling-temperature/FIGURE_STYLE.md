# Project 001 figure style guide

Project supplement to the repository-wide [`VISUAL_STYLE.md`](../../VISUAL_STYLE.md). Use this document when refreshing August-to-July figures or aligning new presentation modules (for example the monthly rolling monitor on a feature branch).

Golden reference render: local snapshot worktree at `~/Documents/hinsawdd-cymru-snapshots/001-pre-monthly-monitor-3188e14` (commit `3188e14`). Compare regenerated PNGs side-by-side before publishing.

Shared constants live in [`figure_style.py`](figure_style.py).

## Canonical figures

| Figure | Generator | Dimensions | Series | Key visual rules |
|---|---|---|---|---|
| Main trend (light) | `analysis.py` → `make_figure()` | 12×6.5 @ 220 DPI PNG + SVG | 142 Aug–Jul periods | Blue thin line, orange 10-period average, grey dotted 1991–2020 ref, 3-line legend upper-left |
| Square dark social | `social_chart.py` | 1080×1080 | same | Red periods, cyan trailing average, grey ref, headline block top-left |
| Standard line chart | `line_chart_variants.py` | 1600×900 | same + Gaussian trend | Seaborn light palette; previous high from prior published period |
| Dark square line | `line_chart_variants.py` | 1080×1080 | same | Dark bg `#040914`; previous-high label uses 2006–07 at 10.32°C, not the current record |
| Stripes / bars | `august_to_july_stripes.py` | per WARMING_STRIPES.md | Aug–Jul anomalies | Published vs provisional final-period label |

## Legend strings (August-to-July)

All three trend-family charts must include:

1. `Individual August-to-July periods`
2. `Trailing 10-year average` (not “10-window” on August-to-July charts)
3. `Derived 1991–2020 reference`

## Monthly refresh checklist

1. Fetch Met Office source (`analysis.py --refresh` or `fetch_source.py`).
2. Run pipeline in order: `analysis.py` → `social_chart.py` → `warming_stripes.py` → `august_to_july_stripes.py` → `line_chart_variants.py`.
3. Verify SVG contains required legend strings (see `tests/test_figure_style.py`).
4. Compare PNG visually against golden files in the snapshot worktree.
5. Run `verify.py` and the full test suite (`pytest -q projects/001-rolling-temperature/tests`).

## Rolling monitor (feature branch)

On `project-001/monthly-monitor`, parallel wording applies:

- `Individual rolling 12-month windows`
- `Trailing 10-window average`
- `Derived 1991–2020 reference`

Light history chart colours should match `make_figure()`; dark square should follow the `social_chart.py` layout family.
