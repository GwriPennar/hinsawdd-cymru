# Methodology

## Scientific objective

Project 005 creates a reproducible observational baseline for measured air quality in Wales. The first implementation focuses on PM2.5 because fine particulate matter is a central smoke-related pollutant while also having many non-fire sources.

The analysis is deliberately source-agnostic: a concentration is measured first; attribution is a later task.

## Primary source

Stage A uses DEFRA UK-AIR pre-formatted annual AURN CSV files:

`https://uk-air.defra.gov.uk/datastore/data_files/site_data/{SITE}_{YEAR}.csv?v=1`

UK-AIR describes these files as one year of automatic monitoring data, updated daily.

For every download the pipeline retains:

- exact CSV bytes;
- source URL;
- retrieval timestamp in UTC;
- SHA-256 digest;
- byte count.

This matters because recent records may later be ratified and revised upstream.

## Station selection

Stage A includes the Welsh AURN sites identified as currently measuring hourly PM2.5. The station registry is frozen in `data/stations.csv` for a run and includes site code, name, environment type, coordinates and UK-AIR ID.

No spatial interpolation is performed. The station map shows monitoring locations only.

## Time handling

UK-AIR files use a `Date` and `Time` field. The parser supports an hour-ending value of `24:00` by representing it internally as midnight at the start of the following timestamp while retaining the original reporting date.

Daily statistics group by the upstream reporting date, so the `24:00` observation remains associated with the intended reporting day.

Times are treated as GMT/UTC for this dataset.

## Pollutants

The parser recognises PM2.5, PM10, nitrogen dioxide (NO2) and ozone (O3). Stage A charts PM2.5 only. Other pollutants are retained for later comparative stages where present.

The parser resolves measurement columns by known UK-AIR names and explicitly ignores status/unit columns.

## Daily aggregation

A daily pollutant mean is published for a station only when at least **18 valid hourly observations** are present for that reporting day. This is a 75% daily capture rule.

Missing, non-numeric and upstream “No data” values are not imputed.

## Analysis windows

Default windows are relative to the latest reporting date actually present in the downloaded data:

- rolling baseline: latest 365 days;
- recent window: latest 70 days.

This avoids pretending that the data are current to the execution date when an upstream station has not reported.

## National interpretation

There is no simple “Wales mean” in Stage A. AURN monitors are not a regular spatial grid and include different environment types. The primary rolling chart therefore shows stations individually.

Any later national aggregate must state its weighting rule explicitly.

## Charts

Canonical figures follow `VISUAL_STYLE.md`: dark background; 1600×900 report/web PNG and SVG; 1080×1080 square PNG and SVG; explicit pollutant unit and time window; visible source and provisional-data note; no generated or decorative data marks.

The first four chart families are rolling-year station time series, recent-window station time series, station distribution comparison and a monitoring-site coordinate map.

## Attribution rule

No peak is attributed to wildfire, traffic, industry, Saharan dust, domestic combustion or meteorology solely from this dataset.

A later event study must triangulate measured concentrations with independent evidence such as fire detections, satellite imagery and meteorology/dispersion data, and must state alternative explanations.

## Validation

Automated tests cover pollutant-column selection, `24:00` timestamp handling, non-numeric missing values, the 18-hour daily completeness rule, exact required raster dimensions and generation of all canonical PNG and SVG chart variants.

The parser/chart suite is testable using synthetic data without network access.
