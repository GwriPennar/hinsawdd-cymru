# Swansea and Gower local watch

Project 006 includes a manual, data-only local FIRMS query for Swansea and the Gower Peninsula. It is intentionally separate from the Wales-wide publication workflow and does not generate maps or images.

## Default area

The first local profile uses this bounding box:

```text
[-4.35, 51.52, -3.85, 51.72]
```

This is a pragmatic Swansea/Gower situational-awareness rectangle, not an administrative boundary.

## Run

Set the existing FIRMS key and run:

```bash
export NASA_FIRMS_MAP_KEY="..."
python projects/006-wildfire-watch/local_watch.py --hours 5
```

The default output root is:

```text
projects/006-wildfire-watch/published/local/swansea-gower/
```

Outputs are data only:

```text
data/derived/detections.csv
data/derived/clustered_detections.csv
data/derived/incidents.csv
data/derived/summary.json
data/raw/<UTC snapshot>/VIIRS_*_NRT.csv
```

`summary.json` records the exact query window, bounding box, detection and cluster counts, latest observation time, successful FIRMS sources, source errors, whether the result is partial-source data, and the retained raw snapshot path.

## Source failure behaviour

The local watch queries `VIIRS_SNPP_NRT`, `VIIRS_NOAA20_NRT` and `VIIRS_NOAA21_NRT` independently. If one source is temporarily unavailable, the run records the failure and continues with the successful sources. If all three fail, the run fails and no derived situational result is presented as valid.

## Interpretation

A FIRMS thermal anomaly is not confirmation of a wildfire. A fire-service deployment may also produce no FIRMS observation, particularly for structural, vehicle or other small/short-lived incidents. The local watch is therefore an additional evidence stream, not an emergency-service incident feed.
