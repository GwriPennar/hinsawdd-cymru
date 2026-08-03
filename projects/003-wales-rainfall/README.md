# 003: Glawiad Cymru

## Wales rainfall since 1836

**Adroddiad canlyniadau / Results report**

Project 003 asks:

> How has Wales-wide rainfall changed since records began, what does the latest complete August-to-July period show, and what does a deliberately simple statistical continuation produce?

The primary evidence is the official Met Office National Climate Information Centre Wales areal rainfall series derived from HadUK-Grid 1 km observations. Monthly rainfall totals begin in 1836.

<!-- BEGIN GENERATED RESULT -->
## Headline results

| Measure | Result |
|---|---:|
| Official monthly source coverage | **1836-01 to 2026-06** |
| Complete August-to-July periods | **189** |
| Derived 1991–2020 August-to-July reference | **1464.8 mm** |
| Latest complete period | **2024-08 to 2025-07** |
| Latest complete rainfall | **1290.2 mm**, 88.1% of reference |
| Current incomplete period | **2025-08 to 2026-06**, 11 published months |
| Current incomplete rainfall | **1538.2 mm**, 112.6% of the like-for-like August–June reference |
| Current partial rank among historical August–June periods | **19 of 190** |
| Full-record trend | **+10.6 mm per decade** |
| Modern trend, 1970 onward | **+31.7 mm per decade** |
| Illustrative 2050 continuation | **1602 mm** |
| Illustrative 2100 continuation | **1760 mm** |

The official Wales series currently stops at June 2026. The August 2025–July 2026 total is therefore **not complete and is not ranked against complete twelve-month periods**. It is compared only with historical August-to-June totals until July is published.

The projection is deliberately secondary. It is a transparent statistical baseline, not a physical rainfall forecast or an official Met Office, UKCP or UKCI projection.

### Wettest complete periods

| Rank | Period | Rainfall | % of 1991–2020 |
|---:|---|---:|---:|
| 1 | 2023-08 to 2024-07 | **1862.5 mm** | 127.2% |
| 2 | 2006-08 to 2007-07 | **1810.4 mm** | 123.6% |
| 3 | 2000-08 to 2001-07 | **1808.6 mm** | 123.5% |
| 4 | 1876-08 to 1877-07 | **1774.1 mm** | 121.1% |
| 5 | 2019-08 to 2020-07 | **1769.4 mm** | 120.8% |
| 6 | 2015-08 to 2016-07 | **1738.6 mm** | 118.7% |
| 7 | 1852-08 to 1853-07 | **1716.3 mm** | 117.2% |
| 8 | 2020-08 to 2021-07 | **1702.3 mm** | 116.2% |
| 9 | 1929-08 to 1930-07 | **1699.9 mm** | 116.1% |
| 10 | 1919-08 to 1920-07 | **1679.6 mm** | 114.7% |

### Driest complete periods

| Rank | Period | Rainfall | % of 1991–2020 |
|---:|---|---:|---:|
| 1 | 1933-08 to 1934-07 | **899.5 mm** | 61.4% |
| 2 | 1975-08 to 1976-07 | **949.2 mm** | 64.8% |
| 3 | 1854-08 to 1855-07 | **964.8 mm** | 65.9% |
| 4 | 1857-08 to 1858-07 | **968.2 mm** | 66.1% |
| 5 | 1955-08 to 1956-07 | **1021.7 mm** | 69.8% |
| 6 | 1853-08 to 1854-07 | **1023.7 mm** | 69.9% |
| 7 | 1855-08 to 1856-07 | **1038.2 mm** | 70.9% |
| 8 | 1844-08 to 1845-07 | **1045.2 mm** | 71.4% |
| 9 | 1895-08 to 1896-07 | **1062.2 mm** | 72.5% |
| 10 | 1920-08 to 1921-07 | **1066.5 mm** | 72.8% |
<!-- END GENERATED RESULT -->

## Main historical chart

![Wales August-to-July rainfall history](figures/wales_august_to_july_rainfall_history.svg)

This chart shows every complete August-to-July rainfall total, the trailing ten-period mean and the derived 1991–2020 reference.

The current period beginning in August 2025 is treated separately because the official country series currently contains data only through June 2026. Its August-to-June total is compared only with historical August-to-June periods. It is not ranked against complete twelve-month totals until July is published.

## Statistical projection chart

![Wales rainfall statistical projection](figures/wales_rainfall_statistical_projection.svg)

The projection is deliberately placed after the historical analysis. It includes:

- a modern-period ordinary least-squares fit using complete published periods ending from 1970 onward;
- a full-record regression sensitivity;
- a robust Theil–Sen modern-period sensitivity;
- a moving-block bootstrap range for uncertainty in the fitted statistical trend;
- fixed-origin ten-year backtests.

> **This is not a physical climate forecast.** It does not represent UKCP, UKCI, future emissions, atmospheric circulation, hydrology or flood risk. It is a transparent baseline for later comparison with official climate-projection ensembles.

## Why rainfall first?

Rainfall is the strongest next variable for a long historical Wales analysis because the official monthly HadUK-Grid country series begins in 1836. Humidity and several related variables begin much later, generally from 1961. A scientifically meaningful drought analysis would also require a defined index, such as SPI or SPEI, rather than treating low rainfall alone as drought.

Project 003 therefore remains focused on precipitation totals. Humidity, soil moisture, evapotranspiration and drought indices should be handled as separate, explicitly defined projects.

## Met Office framework adopted

The project follows the official data boundary:

- source variable: total precipitation amount in millimetres;
- source geography: Wales land-area average from the HadUK-Grid 1 km product;
- monthly totals are summed, not averaged;
- annual reconstructed totals are reconciled against the official annual column;
- the 1991–2020 comparison is expressed in millimetres and as a percentage of the reference;
- provisional or incomplete periods are kept separate from complete published periods;
- the exact source bytes, retrieval metadata and SHA-256 digest are retained.

Official background:

- https://www.metoffice.gov.uk/research/climate/maps-and-data/data/haduk-grid/haduk-grid
- https://www.metoffice.gov.uk/research/climate/maps-and-data/data/haduk-grid/datasets
- https://www.metoffice.gov.uk/research/climate/maps-and-data/about/archives
- https://www.metoffice.gov.uk/pub/data/weather/uk/climate/datasets/Rainfall/date/Wales.txt

## Reproduce

From the repository root:

```bash
python projects/003-wales-rainfall/fetch_source.py \
  --output-dir projects/003-wales-rainfall/data/raw

python projects/003-wales-rainfall/analysis.py \
  --source projects/003-wales-rainfall/data/raw/<retrieved-source>.txt

python projects/003-wales-rainfall/verify.py \
  --source projects/003-wales-rainfall/data/raw/<retrieved-source>.txt \
  --manifest projects/003-wales-rainfall/data/raw/<retrieved-source>.provenance.json
```

## Outputs

### Data

- `data/derived/wales_monthly_rainfall.csv`
- `data/derived/wales_official_annual_and_seasonal_rainfall.csv`
- `data/derived/annual_reconciliation.csv`
- `data/derived/august_to_july_rainfall.csv`
- `data/derived/august_to_june_rainfall.csv`
- `data/derived/seasonal_trends.csv`
- `data/derived/rainfall_statistical_projection.csv`
- `data/derived/backtest_results.csv`
- `data/derived/summary.json`
- `data/derived/independent_verification.json`

### Figures

- `figures/wales_august_to_july_rainfall_history.{png,svg}`
- `figures/wales_rainfall_statistical_projection.{png,svg}`

## Interpretation boundary

This repository analyses a Wales-wide area average. It does not show local rainfall differences, short-duration downpours, river flows, groundwater, soil moisture, flood probability or drought severity. Those require different spatial and physical datasets.

Hinsawdd Cymru is independent. These are reproducible calculations from Met Office data, not official Met Office products or forecasts.
