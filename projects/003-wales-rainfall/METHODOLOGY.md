# Project 003 methodology

## Scientific question

Project 003 measures Wales-wide precipitation totals using the official Met Office HadUK-Grid country series, then asks whether there are detectable long-term changes in complete August-to-July totals and seasons.

A secondary statistical extrapolation is included only as a transparent comparison baseline.

## Source

The source file is the Met Office National Climate Information Centre Wales rainfall areal series:

`https://www.metoffice.gov.uk/pub/data/weather/uk/climate/datasets/Rainfall/date/Wales.txt`

The file states that it contains monthly, seasonal and annual total precipitation for Wales from HadUK-Grid 1 km gridded climate data. The monthly series begins in 1836.

The exact response bytes are retained with:

- retrieval timestamp;
- source `Last updated` value;
- HTTP metadata where available;
- byte count;
- SHA-256 digest;
- an explicit statement that no transformation was applied to the raw snapshot.

## Parsing

The official text file is fixed-width. Blank cells in the most recent incomplete year must remain missing. The parser therefore uses the column positions in the official header rather than splitting only on whitespace.

The parser validates:

- the official source description;
- the 1836 start year;
- expected monthly, seasonal and annual columns;
- non-negative rainfall totals;
- continuous monthly coverage from the first to the latest published month.

## Annual reconciliation

For every complete calendar year, the twelve published monthly totals are summed and compared with the official annual value.

Small differences are expected because the published monthly values are rounded to 0.1 mm before reconstruction. The independent verifier reproduces the reconciliation using `Decimal` arithmetic.

## August-to-July periods

A complete period is the sum of twelve monthly totals from August through the following July. Rainfall totals are additive, so no temperature-style calendar-day weighting is applied.

The first complete equivalent period is August 1836 to July 1837.

The official source currently ends in June 2026. Therefore:

- August 2024 to July 2025 is the latest complete period;
- August 2025 to June 2026 is an incomplete eleven-month period;
- no July value is invented or modelled;
- the current incomplete period is compared only with historical August-to-June totals;
- its rank among complete August-to-July periods is withheld.

## Reference period

The August-to-July 1991–2020 reference is constructed from the official monthly series:

1. calculate the mean January rainfall across 1991–2020;
2. repeat for every calendar month;
3. sum the twelve monthly normals once each.

The August-to-June reference uses the same method but omits July.

Results are reported as:

- total millimetres;
- difference from the reference in millimetres;
- percentage of the 1991–2020 reference.

This follows the Met Office convention of expressing rainfall anomalies as percentages of a climatological average while retaining the actual total.

## Descriptive trends

The historical analysis retains:

- individual complete August-to-July totals;
- trailing ten-period means;
- full-record ordinary least-squares trend;
- modern-period ordinary least-squares trend from period end year 1970 onward;
- modern-period Theil–Sen robust trend;
- separate full-record and modern trends for winter, spring, summer and autumn.

These are descriptive trends. They do not attribute causes or estimate flood or drought risk.

## Statistical extrapolation

The primary illustrative model fits ordinary least squares to complete published August-to-July totals ending from 1970 through the latest complete period.

Sensitivity checks include:

- ordinary least squares across the full record;
- Theil–Sen estimation across the modern period.

A deterministic circular moving-block bootstrap resamples five-period residual blocks. The resulting 2.5th and 97.5th percentiles describe uncertainty in the fitted statistical trend under the model assumptions.

The range does not include:

- emissions-scenario uncertainty;
- climate-model structural uncertainty;
- changes in atmospheric circulation;
- regional downscaling uncertainty;
- future land-use or hydrological change;
- year-to-year weather prediction uncertainty.

It must not be described as an official climate projection.

## Backtesting

Fixed-origin tests fit the modern model using data available through selected historical cutoff years, then compare predictions with the following ten complete periods.

Metrics include:

- annual mean absolute error;
- annual root-mean-square error;
- error in the following ten-period mean.

This tests the limited short-horizon behaviour of the statistical baseline. It does not validate a century-scale physical forecast.

## Independent verification

`verify.py` uses only the Python standard library and `Decimal`. It independently reproduces:

- source digest and coverage;
- annual reconciliation;
- complete and partial period construction;
- 1991–2020 references;
- wettest and driest complete periods;
- current August-to-June rank;
- full-record and modern linear slopes;
- primary 2050 and 2100 extrapolations.

## Scope exclusions

Project 003 does not yet analyse:

- humidity;
- soil moisture;
- evapotranspiration;
- SPI or SPEI drought indices;
- rainfall intensity at hourly or daily scales;
- river discharge;
- groundwater;
- local flood risk.

Those are distinct scientific questions and require additional datasets and methods.
