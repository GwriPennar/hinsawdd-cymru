# 001: Tymheredd cymedrig Awst i Orffennaf

## Wales August-to-July mean temperature

**Research question:** Was the period from 1 August 2025 to 31 July 2026 the warmest equivalent August-to-July period in the Wales temperature record?

<!-- BEGIN GENERATED RESULT -->
## Current result

| Measure | Result |
|---|---:|
| Illustrative July scenario | **18.0°C** |
| August 2025 to July 2026 mean | **10.63°C** |
| Tested scenario range | **10.61°C to 10.65°C** |
| Previous August-to-July high | **10.32°C** |
| July value needed to break that high | **14.33°C** |
| Difference from derived 1991-2020 reference | **+1.21°C** |
| August-to-July rank | **1** |

The exact July Wales area-average is not yet present in the source. This is an **illustrative scenario**, not a Met Office estimate or confidence interval. The ranking is robust because July need only average 14.33°C to exceed the previous high.
<!-- END GENERATED RESULT -->

![Wales August-to-July mean temperature chart](figures/wales_august_to_july_mean_temperature_provisional.svg)

## What is official and what is derived?

**Official Met Office input:** the published monthly Wales areal mean-temperature series, derived from HadUK-Grid.

**Calculated here:** day-weighted August-to-July means, historical rankings, reference-period comparisons and sensitivity scenarios.

**Not yet official:** the final July 2026 Wales area-average. Until it appears in the source series, 18.0°C is used only as an illustrative scenario.

## Suggested public wording

> I looked at the Met Office Wales monthly mean-temperature series and calculated the mean for the 12 months from 1 August 2025 to 31 July 2026, weighting each month by its number of days. The exact result remains provisional until the July Wales figure is published, but the ranking is already clear. July would only need to average 14.33°C for this to become the warmest August-to-July period in the Welsh series, which begins in 1884. If July matches or exceeds the previous published July record of 17.8°C, the 12-month mean will be at least approximately 10.61°C.

This should not be shortened to “Wales has warmed by 2°C”. A one-year anomaly against an older reference period is not an estimate of permanent long-term warming.

## Reproduce

From the repository root:

```bash
python projects/001-rolling-temperature/analysis.py
python projects/001-rolling-temperature/verify.py \
  --source projects/001-rolling-temperature/data/raw/<snapshot>.txt \
  --manifest projects/001-rolling-temperature/data/raw/<snapshot>.provenance.json \
  --primary-summary projects/001-rolling-temperature/data/derived/summary.json \
  --require-annual
pytest
```

Download a new immutable upstream snapshot and rerun:

```bash
python projects/001-rolling-temperature/analysis.py --refresh
```

A refresh writes a new timestamped source snapshot. It does not silently overwrite an earlier source file.

## Documentation

- [`METHODOLOGY.md`](METHODOLOGY.md), the observation-to-grid-to-analysis chain and calculation choices
- [`VALIDATION.md`](VALIDATION.md), source reconciliation, independent rerun and known limitations
- [`data/derived/summary.json`](data/derived/summary.json), machine-readable headline results and provenance
- [`data/derived/annual_reconciliation.csv`](data/derived/annual_reconciliation.csv), monthly reconstruction against the official annual column

## Primary sources

- [Met Office Wales monthly, seasonal and annual mean-temperature series](https://www.metoffice.gov.uk/pub/data/weather/uk/climate/datasets/Tmean/date/Wales.txt)
- [HadUK-Grid methods](https://www.metoffice.gov.uk/research/climate/maps-and-data/data/haduk-grid/methods)
- [HadUK-Grid frequently asked questions](https://www.metoffice.gov.uk/research/climate/maps-and-data/data/haduk-grid/faq)
- [Met Office observations, station standards and quality control](https://weather.metoffice.gov.uk/learn-about/how-forecasts-are-made/observations/obs-critical-for-weather--climate)
- [Reproducible Analytical Pipelines, Code of Practice for Statistics](https://code.statisticsauthority.gov.uk/case-studies/using-reproducible-analytical-pipelines-rap-to-improve-statistics/)

The source data remain Crown copyright and subject to their original licence. This is an independent derived analysis, not an official Met Office statistic.
