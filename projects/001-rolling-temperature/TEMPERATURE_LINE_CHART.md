# Wales August-to-July mean-temperature line charts

These reproducible Project 001 graphics present the validated Wales temperature series in a conventional historical line-chart format while retaining the project's August-to-July annual boundary.

## Standard light view

<a href="figures/wales_august_to_july_mean_temperature_line_chart.png"><img src="figures/wales_august_to_july_mean_temperature_line_chart.png" alt="Wales August-to-July mean-temperature line chart, 1884–85 to 2025–26" width="100%"></a>

[Open the standard chart as SVG](figures/wales_august_to_july_mean_temperature_line_chart.svg)

The standard version uses a restrained Seaborn light palette while retaining the reference, published historical extrema, latest-period guide and descriptive smoothed trend.

## Square dark-mode view

<p align="center"><a href="figures/wales_august_to_july_mean_temperature_line_chart_square_dark.png"><img src="figures/wales_august_to_july_mean_temperature_line_chart_square_dark.png" alt="Square dark-mode Wales August-to-July mean-temperature line chart, 1884–85 to 2025–26" width="78%"></a></p>

[Open the dark-mode chart as SVG](figures/wales_august_to_july_mean_temperature_line_chart_square_dark.svg)

The dark version uses the same underlying values and smoothed trend in a 1080 × 1080 format. It does not perform a separate calculation.

## What the charts represent

Each connected value is one complete twelve-month period:

- August 1884 to July 1885;
- August 1885 to July 1886;
- continuing through August 2025 to July 2026.

The annual boundary is therefore different from a normal January-to-December calendar-year chart. Shifting the boundary allows the latest equivalent period to end in July 2026 while retaining complete twelve-month comparisons.

Both graphics include:

- every August-to-July mean temperature in the validated derived series;
- the existing validated Project 001 1991–2020 reference for the August-to-July target sequence;
- the previous published-input record in 2006–07;
- the latest 2025–26 result using **published July 2026 at 17.8°C**;
- a deterministic seven-year Gaussian-smoothed line to make the broad historical direction easier to see.

The smoothed line is descriptive presentation, not a climate projection, attribution model or formal estimate of the warming rate.

## July 2026 status

The retained Met Office Wales monthly source is published through **August 2026** (`Last updated 01-Sep-2026 11:56`). July 2026 is **17.8°C** in the official monthly table and is used directly by `analysis.py`. Chart footers state this as a published input, not an illustrative scenario.

## Data and method boundary

`line_chart_variants.py` is presentation-layer code. It reads the validated outputs prepared by `analysis.py` and `equivalent_period_chart.py`:

- `data/derived/august_to_july_mean_temperature.csv`;
- `data/derived/summary.json`.

The underlying August-to-July means remain calendar-day weighted. The presentation module does not calculate monthly source values, modify retained raw data or introduce a second scientific method.

## Reproduce

From the repository root:

```bash
python projects/001-rolling-temperature/analysis.py
python projects/001-rolling-temperature/verify.py \
  --source projects/001-rolling-temperature/data/raw/metoffice-wales-tmean-retrieved-2026-09-01T230334Z.txt \
  --manifest projects/001-rolling-temperature/data/raw/metoffice-wales-tmean-retrieved-2026-09-01T230334Z.provenance.json \
  --primary-summary projects/001-rolling-temperature/data/derived/summary.json \
  --require-annual
python projects/001-rolling-temperature/line_chart_variants.py --update-readmes
```

Generated outputs:

- `figures/wales_august_to_july_mean_temperature_line_chart.png`, exactly 1600 × 900;
- `figures/wales_august_to_july_mean_temperature_line_chart.svg`;
- `figures/wales_august_to_july_mean_temperature_line_chart_square_dark.png`, exactly 1080 × 1080;
- `figures/wales_august_to_july_mean_temperature_line_chart_square_dark.svg`;
- `data/derived/wales_august_to_july_temperature_line_chart.csv`.

## Source and independence

Source data: Met Office National Climate Information Centre, Wales monthly HadUK-Grid areal mean-temperature series.

Hinsawdd Cymru is independent. These are reproducible adaptations calculated from Met Office data, not official Met Office products.
