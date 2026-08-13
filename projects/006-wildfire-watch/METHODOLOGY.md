# Project 006 methodology

## 1. Scope

Project 006 builds an inspectable satellite thermal-anomaly tracker for Wales and the wider UK using NASA FIRMS VIIRS near-real-time data. It does not construct a verified wildfire incident register.

The analysis contract deliberately separates four concepts:

1. **FIRMS detection** — one satellite fire/thermal-anomaly pixel supplied by NASA;
2. **normalised detection** — the same record after type/time cleaning in this repository;
3. **thermal-anomaly cluster** — one or more detections linked by the Project 006 space/time heuristic;
4. **verified wildfire** — an external ground claim that Project 006 does not create on its own.

## 2. Source feeds

The live build queries the NASA FIRMS Area API for:

- `VIIRS_SNPP_NRT`;
- `VIIRS_NOAA20_NRT`;
- `VIIRS_NOAA21_NRT`.

The default UK query box is `-8.8,49.7,2.0,61.0`, expressed as west,south,east,north. FIRMS permits a day range of 1–5 days; Project 006 defaults to 2.

A free NASA FIRMS map key is required by the Area API. The build reads it only from `NASA_FIRMS_MAP_KEY` for live fetches.

## 3. Source retention and credential safety

Each live response is written byte-for-byte to `data/raw/<retrieval UTC>/<source>.csv`.

For each response the pipeline records the FIRMS source ID, retrieval timestamp in UTC, SHA-256 of the exact response bytes, byte count, query bounding box, requested day range/date and an API endpoint with the credential replaced by `{MAP_KEY}`.

The map key must never appear in committed provenance, derived CSV, GeoJSON, HTML or logs produced by this code. A failure of one of the three requested feeds fails the live build rather than silently publishing a partial three-satellite view as if it were complete.

## 4. Normalisation

The parser requires the core VIIRS FIRMS fields: `latitude`, `longitude`, `acq_date`, `acq_time`, `satellite`, `instrument`, `confidence`, `version`, `frp`, `daynight`.

Coordinates and FRP are converted to numeric values. Acquisition date and time are combined using NASA's documented zero-padded HHMM convention and represented as timezone-aware UTC timestamps.

FIRMS confidence codes are exposed both unchanged and as readable labels: `l` to low, `n` to nominal and `h` to high.

Invalid coordinates or invalid acquisition timestamps are excluded from the derived record but the source bytes remain preserved. Exact duplicate rows for the same source, satellite, acquisition time and coordinates are removed from the normalised table. Cross-satellite observations are not deduplicated because independent satellite detections are evidence worth retaining.

## 5. Wales MVP watch window

The boolean `in_wales_watch_bbox` uses the rectangle `(-5.6, 51.2, -2.55, 53.5)`.

It is an interface emphasis only. It must never be described as an authoritative Wales boundary or used for precise Welsh national statistics. The field name deliberately says `bbox` rather than `in_wales`.

## 6. Spatial/temporal clustering

The first clustering implementation is intentionally dependency-light and transparent. Two detections are connected when great-circle distance, calculated with the haversine formula, is at most 5 km and acquisition times are no more than 18 hours apart.

Connections are transitive and resolved with a union-find structure. This means A can join B and B can join C even when A and C are not directly within the thresholds.

This is useful for reducing repeated satellite pixels into map-level candidates, but it has consequences: nearby independent events may merge, a long or moving event can link detections across a larger final footprint, parameter changes can split or merge clusters and clusters are not equivalent to fire-service incidents.

The thresholds are therefore exported in `summary.json` and exposed as `--cluster-km` and `--cluster-hours` CLI arguments.

## 7. Cluster summaries

For each cluster the pipeline reports a deterministic run-level ID derived from its earliest retained detection, mean latitude/longitude as a display centroid, detection count, number and names of satellites, FIRMS source IDs, first/latest detection timestamps, duration between those observations, peak and mean FRP where present, highest confidence label present, day/night codes present and whether any member lies in the MVP Wales watch rectangle.

The identifier prefix is `HC-TA` for **Hinsawdd Cymru thermal anomaly**. It deliberately avoids `FIRE` because the cluster is not a confirmed wildfire.

The current ID is stable for a fixed retained input set, not guaranteed stable across rolling live windows. Persistent event identity is a later research problem.

## 8. GeoJSON and map

`incidents.geojson` contains one point feature per thermal-anomaly cluster using the display centroid. `site/index.html` embeds that GeoJSON directly so the data do not require a separate local web server. Leaflet renders the base map and Leaflet MarkerCluster creates numbered display clusters at wider zoom levels.

The map popup repeats the evidence boundary: **thermal-anomaly cluster, not a confirmed wildfire**.

OpenStreetMap tiles and Leaflet assets are loaded at view time from their respective public hosts. A future public deployment should review tile/CDN usage and pin or self-host frontend assets if traffic justifies it.

## 9. Validation

Credential-free tests use small synthetic FIRMS-format fixtures to verify NASA HHMM acquisition-time parsing to UTC, confidence-label mapping, Wales-watch-box semantics, cross-satellite spatial/temporal clustering, cluster evidence fields, GeoJSON production, map generation and warning text, absence of a map key from generated HTML and retained-input failure behaviour.

The GitHub Actions validation job also performs an end-to-end retained-fixture build and checks the expected outputs exist. Synthetic fixture counts are **test evidence only** and must never be presented as real satellite observations.

## 10. NRT versus historical research

Near-real-time data are appropriate for a tracker because timeliness is the purpose of the product. Retrospective scientific analysis should reconcile against NASA Standard Processing when the corresponding period becomes available, because the standard record is the better long-term analysis boundary.

Project 006 will preserve both the exact NRT snapshot used at the time and any later standard-processed reconciliation rather than silently replacing one with the other.

## 11. Attribution rule

Project 006 alone cannot establish that a thermal anomaly caused an air-quality episode. A later attribution claim should require independent agreement among multiple evidence classes, such as authoritative or otherwise credible ground incident evidence, overlapping VIIRS detection location and timing, wind/dispersion evidence of suitable direction and timing, satellite smoke imagery where interpretable, measured ground particulate response and plausible rejection of important alternative sources.

This mirrors Project 005's separation of measurement, QC, event screening and attribution.
