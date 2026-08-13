# Project 006 — Wales Wildfire Watch

## Publication status

**Published first public release — provisional research output.**

This is the first public release of the Wales Wildfire Watch workflow. It is intended as a reproducible research and situational-awareness project, not as an operational emergency-warning service or an official wildfire register.

The underlying NASA FIRMS observations are real public satellite data, but a VIIRS thermal anomaly is **not automatically a wildfire**. Industrial heat, persistent hot sources and other non-wildfire phenomena can appear. The project therefore preserves every observation and keeps interpretation in separate, auditable layers.

The current evidence categories and external-corroboration rules are deliberately provisional. They will be revised as more Welsh incidents, negative controls and official source records are added. Absence of a matching public report must never be interpreted as evidence that no fire exists.

If this project is cited or shared, the safest description is: **a provisional, reproducible map of NASA FIRMS thermal anomalies over Wales, with independent evidence layers for satellite strength and external wildfire corroboration.**

## Question

Where is NASA detecting recent fire/thermal anomalies over Wales, and how can those observations be turned into a reproducible situational-awareness map **without claiming that every hotspot is a wildfire**?

Project 006 is the satellite counterpart to [Project 005 — Wales air quality](../005-wales-air-quality/). Project 005 starts from measured ground-level pollution. Project 006 starts from space-based thermal anomalies and keeps a separate external-incident corroboration layer.

## Pipeline

The current reproducible pipeline is:

**NASA FIRMS VIIRS → retained source CSV + SHA-256 provenance → normalised detections → spatial/temporal clustering → official Wales boundary → candidate-location table → satellite evidence band → external incident correlation → maps + CSV/GeoJSON evidence**

The three default near-real-time feeds are:

- `VIIRS_SNPP_NRT` — Suomi NPP;
- `VIIRS_NOAA20_NRT` — NOAA-20;
- `VIIRS_NOAA21_NRT` — NOAA-21.

NASA's VIIRS active-fire product has a nominal 375 m nadir resolution. FIRMS returns fire/thermal-anomaly pixels, not a verified national wildfire incident register.

## Scientific map

`scientific_map.py` uses the official Welsh Government DataMapWales **Communities (Wales)** boundary in EPSG:4326 and generates the canonical dark Hinsawdd Cymru outputs:

- 1600 × 900 PNG and SVG;
- 1080 × 1080 PNG and SVG;
- `wales_candidate_locations.csv`.

The map is generated programmatically with Python, pandas, Matplotlib and Seaborn. Generative-image tools are not used for scientific plots or data marks.

## Satellite evidence bands

The satellite layer answers only: **how much supporting satellite evidence is present at this location?** It is not a wildfire probability.

Current descriptive bands are:

- **strong satellite evidence** — high FIRMS confidence, at least two satellites, persistence of at least one hour, plus either at least 10 detections or peak FRP of at least 20 MW;
- **plausible** — nominal/high FIRMS confidence plus at least one supporting feature such as repeat detections, multiple satellites or a stronger thermal signal;
- **low** — a weak or isolated observation that does not meet the above rules.

No NASA observation is deleted merely because an industrial or persistent heat source is suspected.

## External corroboration layer

`corroboration.py` adds a **separate** evidence layer using a curated, auditable incident register:

`data/reference/external_wildfire_incidents.csv`

The register prioritises:

1. fire and rescue services;
2. Welsh Government / NRW / police;
3. reputable news reports when useful as a secondary source.

Every record contains an incident name, approximate reported location, incident time window, source class, source URL, publication time, location precision and a short source statement.

Clusters are matched deterministically by distance and time. The default spatial radius is 12 km because many public incident descriptions identify a mountain, valley or locality rather than an ignition coordinate.

The external statuses are deliberately conservative:

- **official_current_match** — an official incident record is spatially close and overlaps the satellite observation window;
- **multiple_source_current_match** — at least two independent external sources are spatially close and overlap the satellite window;
- **known_recent_wildfire_site** — a documented wildfire occurred nearby within the previous 45 days, but this does **not** confirm the current satellite signal;
- **no_current_match** — no current matching record exists in the curated register. This is **not evidence that no fire exists**; public incident reporting is incomplete.

The corroboration run writes:

```text
data/derived/
├── wales_candidate_locations_corroborated.csv
└── external_corroboration_matches.csv
```

This lets the project say, for example, that a cluster is **strong satellite evidence at a known recent wildfire site**, rather than collapsing both facts into a single unsupported “confirmed fire” label.

## Current clustering rule

Nearby VIIRS detections are combined into a thermal-anomaly cluster when they are:

- within **5 km**; and
- within **18 hours**.

Joins are transitive. This is a transparent research/display heuristic and not a NASA fire-event product or a fire-service incident definition.

## Official Wales boundary

The original rectangular MVP screen has been superseded for scientific outputs by the Welsh Government DataMapWales Communities (Wales) dataset. The exact GeoJSON and a provenance manifest are retained during live runs.

## Reproduce

Install the repository environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

For a live NASA build:

```bash
export NASA_FIRMS_MAP_KEY="..."
python projects/006-wildfire-watch/build.py --days 2
python projects/006-wildfire-watch/scientific_map.py \
  --output-root projects/006-wildfire-watch
python projects/006-wildfire-watch/corroboration.py \
  --output-root projects/006-wildfire-watch
```

For credential-free tests:

```bash
pytest -q projects/006-wildfire-watch/tests
```

## Evidence boundary

A VIIRS detection can be caused by an active fire, but FIRMS is a **fire and thermal anomaly** product. Project 006 therefore does not infer ignition cause, burned area, smoke exposure or public-health impact from a marker alone.

Important limitations include:

- satellite overpass timing means this is not continuous observation;
- cloud and smoke can obscure the surface;
- industrial heat and other persistent hot sources can appear;
- the same physical event can generate many pixels and be observed by several satellites;
- FRP is intensity information, not a direct measure of burned area or ground-level pollution;
- an external report may identify a broad locality rather than a precise coordinate;
- the external incident register is curated and incomplete;
- absence from the curated external register does not mean an incident did not occur;
- recent NRT observations may later be superseded by NASA Standard Processing records.

## Relationship to Project 005

A later attribution record can combine multiple independent layers:

**credible ground incident + satellite timing/location + wind/dispersion + smoke evidence + measured PM2.5 response + consideration of alternatives**.

No single layer is sufficient by itself.

## Validation status

The Project 006 GitHub Actions workflow validates the unit tests, retained-fixture pipeline, scientific map renderer and corroboration model. A live repository-secret run has also completed successfully through NASA FIRMS ingestion, official Wales boundary processing, external correlation, output verification and artifact upload.

This validates the software pipeline. It does **not** validate every current thermal anomaly as a wildfire.

## Next stages

1. Expand the curated incident register with additional official current/recent Welsh incidents and preserve source provenance.
2. Add nearest-settlement context alongside official community names.
3. Build recurrence history and persistent/static heat-source screening.
4. Add vegetation/land-cover context.
5. Calculate cross-pass spatial growth and persistence metrics.
6. Connect candidate windows to Project 005 PM2.5 and authoritative wind/dispersion evidence without treating coincidence as causation.
7. Recalibrate the descriptive evidence bands against a growing set of confirmed fires and known non-wildfire heat sources.
8. Introduce scheduled live refresh only after the corroboration and interpretation labels are stable.

See [METHODOLOGY.md](METHODOLOGY.md) and [SOURCES.md](SOURCES.md) for the processing and source contracts.
