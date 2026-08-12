# Methodology

## Scientific objective

Project 005 creates a reproducible observational baseline for measured air quality in Wales. The first implementation focuses on PM2.5 because fine particulate matter is a central smoke-related pollutant while also having many non-fire sources.

The analysis is deliberately source-agnostic: a concentration is measured and quality-checked first; attribution is a later task.

## Primary source

Stage A uses DEFRA UK-AIR pre-formatted annual AURN CSV files:

`https://uk-air.defra.gov.uk/datastore/data_files/site_data/{SITE}_{YEAR}.csv?v=1`

For every download the pipeline retains the exact CSV bytes, source URL, retrieval timestamp in UTC, SHA-256 digest and byte count. Recent records may later be ratified and revised upstream.

The baseline parser also has a `--use-retained` mode so a retained source snapshot can be re-analysed without network access.

## Station selection

Stage A includes the seven Welsh AURN sites retained in `data/stations.csv` as currently measuring hourly PM2.5. Site environment type is carried throughout. No spatial interpolation is performed and no unweighted Wales-wide mean is manufactured from this irregular network.

## Time handling

UK-AIR files use `Date` and `Time` fields and describe the data as GMT hour ending. A `24:00` value is represented internally as midnight at the start of the following physical timestamp while its original reporting date is retained.

Daily statistics group by that reporting date so the hour-ending record remains attached to the intended AURN day.

The dedicated 11 August event module deliberately uses **physical timestamp** instead. This means the `10 August 24:00` record is correctly analysed as midnight at the start of 11 August when examining the overnight transport episode, without changing the daily reporting rule.

## Pollutants and status fields

The parser recognises PM2.5, PM10, nitrogen dioxide (NO2) and ozone (O3), together with the adjacent UK-AIR status field for each pollutant where present.

The raw pollutant observations and upstream status are retained. Stage A charts PM2.5, while PM10 and NO2 are used as contextual checks in the event-screen stage.

## Conservative PM2.5 QC sensitivity

Project 005 does **not** silently delete provisional values. Instead it maintains two parallel series:

- `pm25`: the raw upstream observation;
- `pm25_screened`: a sensitivity series in which a narrowly defined internal-consistency warning is masked.

An hourly observation is flagged only when all of the following are true:

1. the PM2.5 status is provisional (`P` or `P*`);
2. PM2.5 is at least 100 µg/m³;
3. collocated PM10 is available;
4. PM2.5 is more than twice PM10.

This is intentionally conservative. It catches obvious provisional inconsistencies before event attribution while preserving coherent high-particulate episodes in which PM2.5 and PM10 rise together.

The retained baseline currently produces one warning: Swansea Roadside at 01:00 on 14 July 2026, where PM2.5 is 430 µg/m³ and PM10 is 16.425 µg/m³. The raw value remains in the source and combined hourly output. The warning is recorded in `pm25_qc_warnings.csv`.

## Daily aggregation

A daily pollutant mean is published for a station only when at least **18 valid hourly observations** are present for that reporting day, equivalent to 75% daily capture.

The same completeness requirement is applied to the QC-screened PM2.5 sensitivity series. Missing, non-numeric and upstream “No data” values are not imputed.

## Analysis windows

Default windows are relative to the latest reporting date actually present in the downloaded files:

- rolling baseline: latest 365 days;
- recent window: latest 70 days;
- previous comparison window: the immediately preceding 70 days.

This avoids assuming that an annual source file is current to the execution date when the upstream data stop earlier.

## Within-station recent comparison

`pm25_recent_vs_previous.csv` compares each station with itself rather than comparing unlike monitoring environments. The headline comparison uses the QC-screened sensitivity series and also retains the unscreened raw-period means and percentage change.

This makes the effect of any flagged provisional excursion directly visible rather than silently changing the result.

## Site-relative decomposition

To distinguish common regional variation from station-specific excess, each valid station-day is compared with the **same-day median PM2.5 of the other reporting AURN stations**.

At least four peers are required. The derived quantity is:

`site_relative_pm25 = station_pm25_screened - median(other_reporting_stations)`

The pipeline summarises this residual separately for the recent and preceding 70-day windows and also calculates descriptive correlations between station PM2.5 and the same-day other-station median, collocated NO2 and collocated PM10.

These correlations and residuals are observational diagnostics. They are **not source apportionment** and cannot by themselves identify traffic, industry, wildfire or any other emission source.

## Event screen

The recent-period event screen calculates, for each day:

- number of AURN stations with valid QC-screened PM2.5;
- cross-station median and mean PM2.5;
- highest station value and station name;
- number of reporting stations above their own rolling-year 90th percentile.

This helps distinguish broad multi-station episodes from isolated site excursions.

A separate hourly candidate file retains PM2.5 events of at least 50 µg/m³ when collocated PM10 is available and PM2.5/PM10 lies between 0.5 and 1.5. This is a screening device for physically coherent particulate rises, not a pollutant-source classifier.

## July 2026 event-study window

The public July event chart shows QC-screened daily PM2.5 from 13 to 24 July 2026 and marks the reported 19 July initial call for the Blaenavon wildfire.

The marker is contextual only. The analysis explicitly tests the negative-control fact that the strongest broad network episode on 17–18 July predates the fire, and therefore cannot have been caused by it.

`EVENT_STUDY.md` records the later Newport and Cardiff particulate candidates, the available fire-service wind statement and the evidence still required before any wildfire attribution.

## 11 August physical-clock event module

`aug11_event.py` consumes the validated combined hourly output after the baseline run. It does not alter the daily dataset.

The event window begins at **00:00 GMT on 11 August 2026**. For each station it calculates:

- number of valid physical-clock hourly PM2.5 observations on 11 August;
- mean and maximum PM2.5 and time of maximum;
- the station's PM2.5 95th percentile over the preceding 365 physical-clock days;
- count of event hours at or above that station-specific threshold;
- mean PM10 and NO2 over the available event hours;
- mean PM2.5/PM10 ratio where PM10 is positive.

The module writes `pm25_aug11_hourly.csv` and `pm25_aug11_event_summary.csv`, then renders the dedicated 00:00–12:00 GMT event chart. Swansea's missing observations after 05:00 are left missing and explicitly stated on the chart.

This separate physical-clock analysis is necessary because Swansea has too few observations for a valid 11 August daily mean, but the overnight measurements that do exist remain scientifically informative.

## Meteorology boundary

Air Quality in Wales lists modelled wind speed/direction for Swansea Roadside and measured plus modelled wind speed/direction for Port Talbot Margam. Its Openair documentation describes the modelled weather as WRF-based, updated daily, at roughly 10 km × 10 km resolution and representative of regional synoptic conditions rather than local site airflow.

Those data are a planned attribution layer, not an input to the current PM2.5 baseline. Any future wind-conditioned chart must retain that spatial-resolution limitation.

## Charts

Canonical figures follow `VISUAL_STYLE.md`: dark background; 1600×900 report/web PNG and SVG; 1080×1080 square PNG and SVG; explicit units, time window, source and provisional-data note.

Current chart families are:

1. rolling-year station time series;
2. recent-window station time series;
3. rolling-year station distributions;
4. recent versus previous 70-day station comparison;
5. station-relative residual comparison;
6. mid-July event-study timeline;
7. 11 August physical-clock hourly event window;
8. monitoring-site coordinate map.

## Attribution rule

No peak is attributed to wildfire, traffic, industry, Saharan dust, domestic combustion or meteorology solely from this dataset.

A wildfire-attribution statement requires triangulation across ground observations, fire timing, meteorology/dispersion evidence, satellite/fire observations where available and consideration of alternative explanations.

## Validation

Automated tests cover measurement/status parsing, the real UK-AIR preamble and HTML-style pollutant labels, `24:00` handling, the conservative QC rule, daily completeness, screened-versus-raw period comparison, site-relative peer calculations, event-screen logic, the 11 August physical-clock summary, and exact required raster dimensions for all canonical chart families.
