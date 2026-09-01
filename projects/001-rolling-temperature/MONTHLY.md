# Monthly monitor

Project 001 switched to a **monthly rolling 12-month monitor** in September 2026.

## Headline definition

Each refresh uses the latest published Met Office Wales monthly mean-temperature series and calculates every complete **monthly-start 12-month window**. The headline result is always the window whose **final month is the last published calendar month** in the retained source.

Example after the September 2026 refresh (source through **August 2026**):

- headline window: **September 2025 to August 2026**
- mean: **10.65°C**
- rank: **3rd** of **1,701** complete windows

## Archive

The original August-to-July 2025–26 research report is frozen at [`archive/august-to-july-2025-26/`](archive/august-to-july-2025-26/ARCHIVE.md).

## Refresh cadence

- GitHub Actions workflow: [`.github/workflows/refresh-project-001-monthly.yml`](../../.github/workflows/refresh-project-001-monthly.yml)
- Scheduled: **5th of each month, 08:00 UTC**
- Manual: `workflow_dispatch` or locally:

```bash
python projects/001-rolling-temperature/analysis.py --refresh
python projects/001-rolling-temperature/monthly_monitor.py
```

## Outputs

- `data/derived/rolling_12_month_mean_temperature.csv`
- `data/derived/summary.json`
- `figures/wales_rolling_12_month_temperature_history.{png,svg}`
- `figures/wales_rolling_12_month_temperature_square_dark.{png,svg}`
