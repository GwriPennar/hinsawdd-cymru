# Project 006 historical record

Project 006 now supports a cumulative NASA FIRMS record as well as the current two-day situational view.

## Initial backfill

On the first scheduled publication run, `history.py` requests the most recent **60 days** from the NASA FIRMS Area API in chunks of no more than five days, matching the API contract. It queries the three VIIRS NRT sources used by the live project:

- `VIIRS_SNPP_NRT`
- `VIIRS_NOAA20_NRT`
- `VIIRS_NOAA21_NRT`

The retrieval uses the coarse Wales bounding box only to obtain the source data efficiently. The official Welsh Government boundary remains the downstream authority for deciding whether a derived candidate is inside Wales.

Every historical API response is retained under `data/history/raw/` with its source, query dates, safe/redacted endpoint, SHA-256 checksum, byte count and parsed row count recorded in `history_manifest.json`.

The cumulative normalized observation table is `data/history/detections.csv`; `data/history/daily_summary.csv` provides a lightweight day-by-day count for later trend and playback work.

## Daily continuation

The scheduled GitHub Actions workflow runs once per day. It:

1. creates the 60-day historical backfill if it does not already exist;
2. retrieves the latest two-day NASA FIRMS view;
3. rebuilds the official-boundary scientific map;
4. adds direct OpenStreetMap and Google Maps links generated from each retained cluster centroid;
5. runs the external-incident corroboration layer;
6. appends new observations to the cumulative historical table without deleting earlier records;
7. commits the refreshed public evidence and figures back to `main` when data changed.

The map links do not geocode or alter coordinates. They simply open the retained latitude/longitude in an external map. A candidate coordinate is a thermal-anomaly cluster centroid, not a confirmed ignition point.

## Scientific caveat

Near-real-time FIRMS data are operational observations. NASA later replaces NRT records with Standard Processing science-quality data when those products become available. Historical analyses intended for final scientific conclusions should therefore record which processing stream was used and should be reconciled against Standard Processing when practical.

A thermal anomaly remains an observation, not a confirmed wildfire, regardless of how long it remains in the historical record.
