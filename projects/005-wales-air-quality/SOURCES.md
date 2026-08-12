# Sources

## Primary observation source

### DEFRA UK-AIR — Automatic Urban and Rural Network (AURN)

Purpose: Stage A reference-grade hourly pollutant observations and station metadata.

- Pre-formatted annual site files: `https://uk-air.defra.gov.uk/data/flat_files`
- Annual CSV pattern used by the pipeline: `https://uk-air.defra.gov.uk/datastore/data_files/site_data/{SITE}_{YEAR}.csv?v=1`
- AURN site-information pages: `https://uk-air.defra.gov.uk/networks/site-info`

UK-AIR states that its annual automatic-monitoring CSV files are updated daily. The initial station metadata are frozen in `data/stations.csv`.

## Welsh monitoring source for Stage B

### Air Quality in Wales / Welsh Air Quality Database

Purpose: broader Welsh automatic monitoring network, local-authority sites, additional pollutants and Welsh public presentation.

- Measurements: `https://www.airquality.gov.wales/maps-data/measurements`
- Ratification process: `https://www.airquality.gov.wales/maps-data/measurements/ratification-process`

Air Quality in Wales states that automatic networks produce hourly pollutant concentrations. It also explains that near-real-time AURN results are uploaded as provisional data every hour after basic screening and later undergo verification and ratification.

Stage B will ingest this broader network only after the AURN baseline is validated.

## Later attribution sources — not inputs to Stage A

### Met Office

Use: meteorology and atmospheric-dispersion context. The Met Office air-quality product is treated as a forecast/model layer, not as the primary ground-observation source.

### NASA Earthdata Worldview / FIRMS

Use: later fire and smoke-plume observation, including active-fire detections and satellite imagery.

### Copernicus Atmosphere Monitoring Service (CAMS)

Use: later atmospheric composition and transport context.

None of these later sources is used to manufacture or modify the Stage A ground measurements.

## Licensing

UK-AIR pages state that content is available under the Open Government Licence v3.0 except where otherwise stated. Source files remain subject to their upstream terms. Repository analysis code is MIT licensed.
