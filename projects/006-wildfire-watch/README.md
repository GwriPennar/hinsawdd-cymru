# Project 006 — Wales Wildfire Watch

## Publication status

**Published first public release — provisional research output.**

Project 006 is a reproducible research and situational-awareness workflow built from public NASA FIRMS VIIRS observations. A satellite thermal anomaly is not automatically a wildfire, so the project keeps the raw observation, derived cluster, satellite-evidence category and independent external corroboration separate.

## Latest published maps

These graphics are generated programmatically from the published data with Python, pandas, Matplotlib and Seaborn. They are not generative-image outputs.

<a href="published/figures/wales_wildfire_watch_dark.png"><img src="published/figures/wales_wildfire_watch_dark.png" alt="Latest Wales Wildfire Watch scientific map" width="100%"></a>

<p align="center"><a href="published/figures/wales_wildfire_watch_dark_square.png"><img src="published/figures/wales_wildfire_watch_dark_square.png" alt="Latest square Wales Wildfire Watch map" width="72%"></a></p>

The current published two-day run contains **1,660 VIIRS detections** and **23 derived candidate clusters inside the official Wales boundary**. The latest observation is **13 August 2026 at 14:22 UTC**. These are thermal anomalies, not a confirmed wildfire count.

## Data pipeline

**NASA FIRMS VIIRS → retained source data and provenance → normalised detections → 5 km / 18 hour clustering → official Welsh Government boundary → candidate locations → satellite evidence → external corroboration → published maps and CSV/GeoJSON evidence**

The three feeds are `VIIRS_SNPP_NRT`, `VIIRS_NOAA20_NRT` and `VIIRS_NOAA21_NRT`. NASA's nominal 375 m VIIRS pixel size is a product resolution, not a GPS-accuracy claim.

The official location label comes from the Welsh Government DataMapWales **Communities (Wales)** boundary. Each published candidate also receives direct OpenStreetMap and Google Maps links to its retained cluster centroid.

## Historical record

The first automated publication run completed a **60-day backfill**. The cumulative record currently contains **3,177 normalized observations from 15 June to 13 August 2026**.

Historical outputs are retained under `data/history/`, including `detections.csv`, `daily_summary.csv`, provenance and raw source responses. See [HISTORY.md](HISTORY.md).

## Daily publication

A GitHub Actions workflow now runs daily. It retrieves the latest FIRMS data, rebuilds the scientific map, adds location links, runs external corroboration, appends new observations to the cumulative history and commits changed public outputs back to `main`.

## Evidence interpretation

- **strong satellite evidence** — repeated and persistent multi-satellite evidence meeting the documented thresholds;
- **plausible** — a real thermal signal with supporting repetition, multiple satellites or stronger intensity;
- **low** — weak or isolated satellite evidence.

External reports remain a separate evidence layer. A recent known fire near a cluster does not prove the current satellite signal is the same event, and absence of a public report is not evidence that no fire exists.

## Reproduce and validate

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q projects/006-wildfire-watch/tests
```

A live run additionally requires `NASA_FIRMS_MAP_KEY`.

## Next stages

Next work includes friendlier nearest-settlement labels, recurrence/static-heat screening, vegetation context, a time-series/playback view, and later reconciliation of NRT history against NASA Standard Processing.

See [METHODOLOGY.md](METHODOLOGY.md), [SOURCES.md](SOURCES.md) and [HISTORY.md](HISTORY.md) for the full contracts and caveats.
