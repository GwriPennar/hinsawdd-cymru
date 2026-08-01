# 001: Tymheredd cymedrig Awst i Orffennaf

## Wales August-to-July mean temperature

**Research question:** Was the period from 1 August 2025 to 31 July 2026 the warmest equivalent August-to-July period in the Wales temperature record?

## Result

**Yes. The result is already robust, although the precise value remains provisional.**

Using the Met Office Wales monthly mean-temperature series, weighted by the number of days in each month:

| Measure | Result |
|---|---:|
| Central scenario, with July 2026 at 18.0°C | **10.63°C** |
| Scenario range, with July from 17.8°C to 18.3°C | **10.61°C to 10.65°C** |
| Previous highest August-to-July period, 2006-07 | **10.32°C** |
| July 2026 value needed merely to exceed that previous period | **14.33°C** |
| Difference from the reconstructed 1991-2020 baseline | **+1.21°C** |
| Difference from the reconstructed 1961-1990 baseline | **+2.02°C** |

The Met Office reported on 31 July that Wales was tracking its warmest July for mean temperature through 30 July. The exact July area-average had not yet been published. This project therefore does not invent an official value: it shows a central scenario and a sensitivity range.

The important result is not sensitive to the final few hundredths. July would only need to average **14.33°C** for August 2025 to July 2026 to exceed the previous August-to-July high. The Met Office's own provisional assessment makes clear that July was far warmer than that threshold.

Under the central 18.0°C scenario, this period ranks:

- **1st** among equivalent August-to-July periods in the series;
- **4th** among every possible monthly-start 12-month window. The three warmer overlapping windows all ended in spring or early summer 2007.

![Wales August-to-July mean temperature chart](figures/wales_august_to_july_mean_temperature_provisional.svg)

## Suggested public wording

> I looked at the Met Office Wales temperature series and calculated the mean for the 12 months from 1 August 2025 to 31 July 2026, weighting each month by its number of days. The precise July figure is still provisional, but the result is clear: this appears to be the warmest August-to-July period in the Welsh record, which begins in 1884. A reasonable provisional estimate is about 10.63°C, around 1.2°C above the 1991-2020 average for the same sequence of months.

This should not be shortened to “Wales has warmed by 2°C”. The +2.02°C figure is the anomaly of one exceptional 12-month period against the older 1961-1990 reference period, not an estimate of the permanent long-term warming level.

## Method

1. Use the Met Office National Climate Information Centre's monthly Wales mean-temperature series, beginning in 1884.
2. Use the Wales **areal average**, derived from HadUK-Grid, rather than averaging a selection of weather stations.
3. Construct every complete August-to-July period.
4. Weight each monthly mean by the number of calendar days in that month:

   ```text
   period mean = sum(monthly mean × days in month) / total days
   ```

5. Rank equivalent August-to-July periods separately from all possible monthly-start 12-month windows.
6. Calculate reference values from the published monthly series for 1961-1990 and 1991-2020.
7. Keep the unpublished July 2026 value explicit as a scenario until the official monthly series is updated.

The Met Office does not calculate the Wales value by giving every weather station an equal vote. Station observations inform regression and interpolation across a 1 km grid, taking account of factors including altitude, terrain, coastal influence and urban land use. The grid cells within Wales are then averaged to obtain the national areal value.

The monthly HadUK-Grid product is its own interpolation exercise. It should therefore be preferred here to reconstructing a monthly national value from separate daily grid files.

## Precision and limitations

The public monthly series is rounded to one decimal place. Calculations from these published values can differ by a few hundredths of a degree from calculations using the underlying unrounded grid data. This does not affect the August-to-July ranking: the gap from the previous period is approximately 0.30°C even in the lowest July scenario tested.

The retained raw snapshot contains official published months through June 2026. July 2026 is not inserted into that source file. It is added in memory by the analysis as an explicitly labelled scenario.

## Reproduce

From the repository root:

```bash
python projects/001-rolling-temperature/analysis.py
pytest
```

Use a different July scenario:

```bash
python projects/001-rolling-temperature/analysis.py --july-2026 18.1
```

Refresh from the live Met Office series and rerun:

```bash
python projects/001-rolling-temperature/analysis.py --refresh
```

When the live series contains July 2026, the script uses the published value rather than the provisional central scenario.

## Outputs

- [`data/derived/summary.json`](data/derived/summary.json), headline figures and provenance
- [`data/derived/august_to_july_mean_temperature.csv`](data/derived/august_to_july_mean_temperature.csv), all equivalent periods
- `data/derived/all_rolling_12_month_windows.csv`, generated on each run for every monthly-start window
- [`data/derived/july_2026_sensitivity.csv`](data/derived/july_2026_sensitivity.csv), tested July scenarios
- [`figures/wales_august_to_july_mean_temperature_provisional.svg`](figures/wales_august_to_july_mean_temperature_provisional.svg), public graphic

## Primary sources

- Met Office, *Monthly, seasonal and annual mean air temperature for Wales*.
- Met Office, *HadUK-Grid Methods* and *HadUK-Grid Frequently Asked Questions*.
- Met Office, *An early look at the July statistics: just how dry has it been?*, 31 July 2026.

The source snapshot records its source URL, update time and retrieval date. Its SHA-256 digest is included in `summary.json`.

## Licensing and attribution

The Met Office states that HadUK-Grid is available under the Open Government Licence and asks users to acknowledge the source. The source data remain Crown copyright. The code in this repository is MIT licensed.

This is an independent derived analysis, not an official Met Office statistic.
