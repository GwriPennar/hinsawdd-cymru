# Methodology

## Scope

This project answers one narrow question: how the mean air temperature for Wales from August 2025 through July 2026 compares with earlier August-to-July periods in the published record.

It does not recreate the Met Office station network or the HadUK-Grid interpolation. It begins with the Met Office's published Wales areal series and performs a secondary, reproducible calculation.

## Provenance chain

```text
Weather-station instruments
        ↓
Met Office site and observation quality control
        ↓
Monthly station observations
        ↓
HadUK-Grid regression and interpolation to a 1 km grid
        ↓
Average of 1 km land grid cells within Wales
        ↓
Published Wales monthly areal mean-temperature series
        ↓
Hinsawdd Cymru day-weighted 12-month calculation
```

The Met Office states that observations from the UK land surface network inform regression and interpolation across a 1 km grid. Factors include latitude, longitude, altitude, terrain, coastal influence and urban land use. Regional values are averages of the 1 km cells within the specified geographical region.

This avoids treating each weather station as an equally weighted vote and reduces sensitivity to stations opening or closing.

## Observation standards and upstream quality control

The Met Office reports that around 350 UK observation sites report daily. Stations follow World Meteorological Organization guidance, are inspected and monitored, and are compared with neighbouring sites when unusual behaviour appears. Equipment is checked, calibrated and replaced when faulty or approaching tolerance limits.

HadUK-Grid applies quality control that corrects or removes erroneous station observations. The Met Office reports a verification RMSE of 0.36°C for monthly mean-temperature grids across 12 test months. That value describes grid prediction performance at verification stations. It is **not** used here as an uncertainty interval for the Wales national area-average.

## Why the monthly Wales series is the correct input

The research question is monthly and national. The official monthly Wales area-average is therefore preferable to:

- averaging a hand-selected group of stations;
- averaging every station equally;
- rebuilding a monthly national figure from daily grid files.

The Met Office notes that monthly grids are generated independently and are not necessarily identical to an average of the corresponding daily grids.

## Source preservation

A network refresh stores the exact HTTP response bytes without altering whitespace, columns or metadata. Each immutable snapshot has a neighbouring provenance manifest recording:

- source URL;
- retrieval time in UTC;
- source `Last updated` value;
- SHA-256 digest;
- byte count;
- HTTP metadata where available;
- confirmation that no transformation was applied.

Parsing produces a separate normalized monthly CSV under `data/derived`. Raw and derived data are never conflated.

## Period calculation

For each complete August-to-July period:

```text
period mean = Σ(monthly mean × calendar days in month) / Σ(calendar days)
```

Months are weighted by their number of days. Leap-year periods therefore contain 366 days where appropriate.

The calculation uses the published monthly values, which are rounded to 0.1°C. Results can consequently differ by a few hundredths from calculations using the unrounded gridded values. Headline values are reported to 0.01°C and anomalies are described approximately.

## Historical comparisons

Two rankings are produced:

1. equivalent August-to-July periods;
2. every possible complete monthly-start 12-month window.

These answer different questions and are kept separate.

## Reference periods

The project derives monthly reference values from the public monthly series for 1961-1990 and 1991-2020. For each calendar month, it takes the arithmetic mean of the 30 corresponding published monthly area values, matching the Met Office description that climatological monthly grids are averaged across the reference years. The August-to-July sequence is then weighted by the number of days in its months.

These are repository-derived values from rounded public inputs, not replacements for official Met Office climatological products.

## Provisional July handling

If July 2026 is absent from the official source:

- no value is inserted into the retained source file;
- the analysis adds a clearly labelled scenario in memory;
- the central value is called an **illustrative scenario**, not an estimate;
- a sensitivity range is published;
- the break-even July value needed to exceed the previous record is calculated.

When the official July value appears, the analysis uses it automatically.

## Independent verification

`verify.py` is a second implementation using only the Python standard library and `Decimal`. It does not import the primary analysis module or pandas. It independently:

- parses the source;
- checks monthly continuity;
- calculates all August-to-July periods;
- identifies the previous record;
- calculates the break-even July value;
- reconciles reconstructed annual means against the official annual column;
- compares its results with the primary `summary.json`.

Agreement between the two implementations is a meaningful executable rerun. A review by another person or model can supplement this, but does not replace it.
