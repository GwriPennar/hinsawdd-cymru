# Relative humidity source plan

**Status:** awaiting an official CEDA `hurs` source snapshot or authenticated CI access; no substitute dataset will be used.

## Purpose

Add a reproducible Wales-wide mean relative-humidity history using the same scientific and presentation boundaries as the temperature and rainfall projects.

## Official variable

- HadUK-Grid variable: `hurs`
- definition: mean relative humidity over the calendar month, season or year
- unit in Met Office documentation: percent
- observational start year: 1961
- target geography: Wales country area average
- reference period: 1991–2020

The current country release is:

- **HadUK-Grid Climate Observations by UK countries, v1.3.2.ceda (1836–2025)**
- DOI: `10.5285/ca4c331d666f4395b1346db9070094ab`
- CEDA catalogue: `https://catalogue.ceda.ac.uk/uuid/ca4c331d666f4395b1346db9070094ab/`

CEDA requires a registered user session to access the NetCDF files. The repository will not substitute a lower-authority global reanalysis or scrape values without an auditable source snapshot.

## Required source handoff

One of the following is needed before implementation can be completed:

1. a downloaded Wales country `hurs` NetCDF file from the cited release; or
2. CEDA credentials/secrets configured for a reproducible CI download that does not expose credentials.

The retained source must include:

- exact upstream bytes;
- original filename and CEDA path;
- dataset version and DOI;
- retrieval timestamp;
- byte count and SHA-256 digest;
- licence and citation text.

## Planned calculations

1. Validate NetCDF variable name, units, coordinates, calendar and country label.
2. Extract the Wales monthly mean relative-humidity series from 1961 onward.
3. Reconcile monthly values with any supplied annual series.
4. Calculate calendar-year and August-to-July means using calendar-day weighting.
5. Derive 1991–2020 monthly normals and equivalent-period reference.
6. Report actual relative humidity in percent and anomalies in percentage points.
7. Produce trailing ten-period means and descriptive full/modern trends.
8. Backtest any statistical continuation before publication.

## Planned dark chart suite

Every chart will have 1600 × 900 and 1080 × 1080 PNG/SVG variants:

- Wales August-to-July relative-humidity history;
- relative-humidity anomaly bars;
- monthly or seasonal humidity history, selected after inspecting the data;
- illustrative statistical continuation with sensitivity checks.

## Interpretation boundary

Relative humidity is temperature-dependent and is not a standalone measure of atmospheric water content, rainfall deficit, soil moisture or drought. The project will not label lower relative humidity as formal drought without an explicitly defined drought method and corroborating variables.

## Acceptance criteria

- official HadUK-Grid country source only;
- source provenance and digest retained;
- independent reconstruction check;
- no missing periods silently filled;
- 1991–2020 reference reproduced transparently;
- dark wide and square outputs tested for dimensions and labels;
- statistical continuation clearly separated from physical projections;
- GitHub Actions validation and retained evidence.
