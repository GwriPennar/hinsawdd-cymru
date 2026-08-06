# Project 003 methodology

## Scientific questions

Project 003 measures Wales-wide rainfall totals and rain-day frequency using official Met Office HadUK-Grid country series. It separates three observational scales:

- individual calendar months, currently with a dedicated July history;
- complete August-to-July periods;
- descriptive long-term trends and a secondary statistical continuation.

A low-rainfall month is not automatically described as a complete-year drought, and neither rainfall total nor relative humidity alone is treated as a formal drought index.

## Official sources

### Rainfall

`https://www.metoffice.gov.uk/pub/data/weather/uk/climate/datasets/Rainfall/date/Wales.txt`

The monthly Wales area-average series begins in 1836 and reports total precipitation in millimetres.

### Rain days

`https://www.metoffice.gov.uk/pub/data/weather/uk/climate/datasets/Raindays1mm/date/Wales.txt`

The monthly Wales area-average series begins in 1891 and reports the number of days with precipitation amount at least 1 mm.

The exact HTTP response bytes are retained for both sources with retrieval timestamp, upstream `Last updated` value, byte count, SHA-256 digest and a statement that the raw snapshot is untransformed.

## Parsing and continuity

Both official text files are fixed-width. The parser uses the official column positions rather than whitespace splitting so that blank recent months remain missing.

Validation checks include:

- the metric-specific source description;
- expected monthly, seasonal and annual columns;
- continuous monthly coverage from the first to latest published month;
- a valid source update field;
- separate source identity checks so rainfall cannot be mistaken for rain days.

## August-to-July construction

A complete period sums the twelve monthly values from August through the following July.

- rainfall totals are additive in millimetres;
- rain-day counts are additive in days;
- no temperature-style calendar-day weighting is applied;
- only periods containing all twelve published months are retained.

With the source updated on 3 August 2026, the latest complete period is August 2025 to July 2026.

## July history

The July chart uses the official July rainfall value from every available year. Each value is compared with the mean July rainfall for 1991–2020.

The dryness rank is ascending: the smallest July rainfall receives rank 1. Ties use the minimum shared rank.

## Reference period

For each metric:

1. calculate the mean January value across 1991–2020;
2. repeat for every calendar month;
3. sum the twelve monthly normals for an August-to-July reference.

For the dedicated July chart, only the 1991–2020 July normal is used.

Results are reported as actual values and percentages of the relevant reference. The August-to-July dryness chart uses:

`100 × observed total / reference total − 100`

This is a precipitation anomaly, not SPI, SPEI or an operational drought declaration.

## Rain-day frequency

The rain-day series complements total rainfall by asking how many days recorded at least 1 mm. It does not measure:

- rainfall intensity within a wet day;
- the spacing or persistence of consecutive dry days;
- soil-moisture deficit;
- river flow or reservoir storage.

Those require daily sequences or other physical datasets.

## Descriptive trends

The current analysis retains:

- individual complete August-to-July totals;
- trailing ten-period means;
- full-record ordinary least-squares rainfall trend;
- modern ordinary least-squares rainfall trend from period end year 1970 onward;
- modern Theil-Sen sensitivity.

These trends are descriptive. The low coefficient of determination and substantial year-to-year variability are published rather than hidden.

## Statistical continuation

The primary illustrative continuation fits ordinary least squares to complete August-to-July rainfall totals ending from 1970 onward.

Sensitivity checks include full-record ordinary least squares and modern Theil-Sen estimation. A deterministic circular moving-block bootstrap resamples five-period residual blocks to form a 95% trend-fit range.

The continuation does not include emissions scenarios, climate-model structure, future atmospheric circulation, regional downscaling, hydrology or year-to-year predictive skill. It must not be presented as an official climate projection.

## Dark publication standard

All newly published Project 003 charts use the same dark visual system:

- background `#080c16`;
- plot panel `#0f172a`;
- restrained grid and text hierarchy;
- 1600 × 900 widescreen PNG/SVG;
- 1080 × 1080 square PNG/SVG;
- source, update date and 1991–2020 reference on every figure.

Earlier light outputs remain for provenance but are not the default presentation layer.

## Independent verification

`verify_dark.py` uses the Python standard library and `Decimal` independently of pandas and NumPy. It checks:

- both source manifests and SHA-256 digests;
- source update fields and coverage;
- complete August-to-July construction;
- rainfall, July and rain-day references;
- latest rainfall and rain-day totals;
- July 2026 value, rank and comparison count;
- generated summary values against an independent reconstruction from the raw sources;
- presence, exact dimensions and dark background of all five wide/square figure pairs.

## Relative humidity boundary

HadUK-Grid mean relative humidity (`hurs`) begins in 1961. The current country release is distributed as NetCDF through the registered CEDA service. It is deliberately handled as a separate source-ingestion task so that provenance, units, temporal aggregation and missing-data behaviour can be verified before charting or extrapolation.

## Scope exclusions

Project 003 does not claim to measure local drought severity, soil moisture, evapotranspiration, river discharge, groundwater, reservoir status, rainfall intensity, flood probability or crop stress. Formal SPI/SPEI work and humidity are separate defined extensions.
