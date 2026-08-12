# Sources

## Primary observation source

### DEFRA UK-AIR — Automatic Urban and Rural Network (AURN)

Purpose: Stage A reference-grade hourly pollutant observations and station metadata.

- Pre-formatted annual site files: `https://uk-air.defra.gov.uk/data/flat_files`
- Annual CSV pattern used by the pipeline: `https://uk-air.defra.gov.uk/datastore/data_files/site_data/{SITE}_{YEAR}.csv?v=1`
- AURN site-information pages: `https://uk-air.defra.gov.uk/networks/site-info`

The pipeline retains exact downloaded source bytes and SHA-256 provenance records because recent AURN values can later be verified, ratified and revised.

## Welsh monitoring and meteorological context

### Air Quality in Wales / Welsh Air Quality Database

Purpose: broader Welsh automatic network, site metadata, provisional/ratified status context and the preferred site-linked meteorological layer for later attribution.

- Measurements: `https://www.airquality.gov.wales/maps-data/measurements`
- Data download: `https://www.airquality.gov.wales/maps-data/measurements/downloadsubmit-data`
- Ratification process: `https://www.airquality.gov.wales/maps-data/measurements/ratification-process`
- Openair introduction: `https://www.airquality.gov.wales/maps-data/openair-introduction`
- Swansea Roadside: `https://www.airquality.gov.wales/air-pollution/site/SWA1`
- Port Talbot Margam: `https://www.airquality.gov.wales/air-pollution/site/PT4`

Air Quality in Wales describes automatic values as provisional near real time before later verification/ratification. Its site metadata list modelled wind speed and direction for Swansea Roadside and measured plus modelled wind speed/direction for Port Talbot Margam.

The Openair documentation states that modelled meteorology supplied for air-quality analysis is WRF-based, updated daily and uses an approximately 10 km × 10 km grid. It represents regional synoptic conditions and should not be treated as local site airflow.

The broader local-authority monitoring network remains a later Stage B ingestion task; it is not mixed into the seven-site AURN reference baseline without explicit network/site metadata.

## Blaenavon wildfire timeline

### South Wales Fire and Rescue Service reporting via ITV Cymru Wales

Purpose: incident timing, fire extent, smoke and contemporaneous wind-direction statement.

- `https://www.itv.com/news/wales/2026-07-21/firefighters-tackling-significant-wildfire-in-blaenavon`

The 21 July report quotes SWFRS as saying that the initial call was received on Sunday evening, corresponding to 19 July 2026; the fire covered around 80 hectares; smoke had been significant at times; and the then-current wind direction was expected to affect Nant-y-Glo and Brynmawr.

This is used only as an external incident timeline. It does not alter or label any AURN observation.

### Welsh Government wildfire update

Purpose: independent official confirmation that Blaenavon remained a significant ongoing incident and was being managed through a multi-agency response.

- `https://media.service.gov.wales/news/update-from-the-cabinet-minister-for-local-government-housing-and-planning-sian-gwenllian-on-wildfires-across-wales`

The 23 July 2026 update identifies Blaenavon and Rhinogydd as significant fires and describes the coordinated response.

## Satellite layer — reserved for attribution

### NASA Earthdata Worldview / FIRMS

Purpose: active-fire detections, hotspot context and satellite imagery of visible smoke/plume structure.

- Worldview: `https://worldview.earthdata.nasa.gov/`
- FIRMS: `https://firms.modaps.eosdis.nasa.gov/`

Satellite imagery is independent spatial evidence; it is not treated as a ground-level concentration measurement.

## Meteorology and dispersion — later attribution sources

### Met Office

Use: weather observations/analysis and atmospheric-dispersion context. The Met Office air-quality product is treated as a forecast/model layer, not as the primary ground-observation source.

### Copernicus Atmosphere Monitoring Service (CAMS)

Use: later atmospheric composition and transport context where it adds independent evidence.

None of these later sources is used to manufacture or modify the Stage A ground measurements.

## Licensing

UK-AIR and relevant UK public-sector source material are used subject to their upstream terms, including the Open Government Licence where stated. Repository analysis code is MIT licensed.
