# Project 006 — Wales Wildfire Watch

## Question

Where is NASA detecting recent fire/thermal anomalies over Wales and the wider UK, and how can repeated satellite detections be turned into an inspectable public map **without claiming that every hotspot is a wildfire**?

Project 006 is the satellite counterpart to [Project 005 — Wales air quality](../005-wales-air-quality/). Project 005 starts from measured ground-level pollution. Project 006 starts from space-based thermal anomalies. A later attribution stage can ask whether timing, wind, smoke imagery, fire-service reports and measured PM2.5 line up.

## Stage A — working MVP

The first build is implemented as a reproducible NASA FIRMS pipeline:

**NASA FIRMS VIIRS → retained source CSV + SHA-256 provenance → normalised detections → spatial/temporal clustering → GeoJSON + interactive Leaflet map**

The three default near-real-time feeds are:

- `VIIRS_SNPP_NRT` — Suomi NPP;
- `VIIRS_NOAA20_NRT` — NOAA-20;
- `VIIRS_NOAA21_NRT` — NOAA-21.

NASA's VIIRS active-fire product has a nominal 375 m nadir resolution. FIRMS returns fire/thermal-anomaly pixels, not a verified national wildfire incident register.

## What the map means

The generated `site/index.html` is centred on Wales but queries the wider UK by default. It has two distinct kinds of grouping:

1. **Scientific grouping:** nearby VIIRS detections close in time are combined into a *thermal-anomaly cluster* using the explicit heuristic below.
2. **Display grouping:** Leaflet MarkerCluster combines nearby map markers into numbered circles when zoomed out, in the same broad interaction pattern as public fire-tracker maps.

Clicking a marker shows the cluster ID, number of detections, satellites, first/latest detection time, peak Fire Radiative Power (FRP) and highest FIRMS confidence label present.

Every popup states: **thermal-anomaly cluster, not a confirmed wildfire.**

## Current clustering rule

Stage A uses a deliberately simple and inspectable rule:

- detections are joined when they are within **5 km**;
- and within **18 hours**;
- joins are transitive, so a chain of compatible detections becomes one cluster;
- the default parameters are reported in `summary.json` and can be changed from the command line.

This is a display/research heuristic, not a NASA fire-event product and not a fire-service incident definition. It will be calibrated against known Welsh incidents before it is treated as anything stronger.

## Wales watch window

The MVP highlights a rectangular Wales watch window:

`west -5.6, south 51.2, east -2.55, north 53.5`

That rectangle is **not the legal or cartographic boundary of Wales** and may include small neighbouring areas. It exists only to make the first build usable without adding a heavyweight GIS dependency or silently embedding an uncited boundary. Stage B will replace it with a checksum-pinned authoritative Wales boundary.

## Outputs

A live run writes immutable source snapshots under `data/raw/<UTC timestamp>/` and creates:

```text
data/derived/
├── detections.csv
├── clustered_detections.csv
├── incidents.csv
├── incidents.geojson
└── summary.json

site/
└── index.html
```

The raw provenance JSON stores the FIRMS source, retrieval time, checksum, query window and a **redacted API endpoint**. The NASA map key is never written to provenance or generated HTML.

## Reproduce

Install the repository environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Request a free FIRMS `MAP_KEY` from NASA and expose it as an environment variable:

```bash
export NASA_FIRMS_MAP_KEY="..."
python projects/006-wildfire-watch/build.py --days 2
```

The NASA FIRMS Area API supports day ranges from 1 to 5. The default query is the UK bounding box and the most recent two days.

To reproduce the derived outputs without calling NASA again, point the build at a retained snapshot:

```bash
python projects/006-wildfire-watch/build.py \
  --input-dir projects/006-wildfire-watch/data/raw/20260813T120000Z
```

To test the project without credentials or network access:

```bash
pytest -q projects/006-wildfire-watch/tests
python projects/006-wildfire-watch/build.py \
  --input-dir projects/006-wildfire-watch/tests/fixtures \
  --output-root /tmp/hinsawdd-cymru-wildfire-watch
```

## Evidence boundary

A VIIRS detection can be caused by an active fire, but the dataset is a **fire and thermal anomaly** product. Project 006 therefore does not infer ignition cause, fire size, smoke exposure or public-health impact from a marker alone.

Important limitations include:

- satellite overpass timing means this is not continuous observation;
- cloud and smoke can obscure the surface;
- industrial heat and other persistent hot sources can appear;
- the same physical event can generate many pixels and be observed by several satellites;
- FRP is useful intensity information but is not a direct measure of burned area or ground-level pollution;
- recent NRT observations may later be superseded by NASA Standard Processing records.

## Relationship to Project 005

Project 005 already establishes the ground-observation side of the question: measured Welsh AURN PM2.5, event screening and a strict separation between measurement and attribution.

Project 006 provides one of the independent evidence layers needed for the next step. A future wildfire-attribution record should require agreement between several layers, for example:

**credible ground incident + satellite timing/location + wind/dispersion + smoke evidence + measured air-quality response + consideration of alternatives**.

No single layer is sufficient by itself.

## Live deployment status

The code, synthetic fixtures, provenance model, clustering, GeoJSON and interactive map generator are implemented. The repository does **not** contain a NASA credential. A live automated refresh can be enabled once `NASA_FIRMS_MAP_KEY` is added as a GitHub Actions secret; the validation workflow deliberately remains credential-free.

## Next stages

1. Replace the rectangular Wales watch window with an authoritative national boundary.
2. Add a documented persistent/static heat-source screen so industrial anomalies are not casually presented as fire candidates.
3. Validate the clustering parameters against known Welsh wildfire episodes and negative controls.
4. Reconcile historical NRT detections with NASA Standard Processing data when available.
5. Join Project 006 candidates to Project 005 PM2.5 event windows and authoritative wind data, without collapsing coincidence into causation.
6. Add verified incident references from fire services or other authoritative ground sources as a separate evidence class.
7. Only then consider a continuously refreshed public deployment.

See [METHODOLOGY.md](METHODOLOGY.md) for the processing contract and [SOURCES.md](SOURCES.md) for the primary-source register.
