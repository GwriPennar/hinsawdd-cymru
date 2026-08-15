# Project 006 successful correlations

Registry of cases where a NASA FIRMS thermal anomaly was later tied to an independently reported incident.

Machine-readable table: [`data/reference/successful_correlations.csv`](data/reference/successful_correlations.csv)

External incident sources remain in [`data/reference/external_wildfire_incidents.csv`](data/reference/external_wildfire_incidents.csv). That file name is historical; rows may include structure fires when they corroborate a thermal anomaly.

## Evidence rule

A successful correlation means:

1. a retained FIRMS detection (source, time, lat/lon, FRP/confidence);
2. an independent external report (preferably fire service);
3. close spatial match and overlapping time window;
4. explicit incident type (`structure_fire`, `wildfire`, etc.).

It does **not** reclassify the FIRMS pixel as a confirmed wildfire.

## Current entries

### CORR-2026-LANGROVE-HC-001 — Langrove Health Club, Parkmill

**News (brief):** On the evening of 14 August 2026 a fire started in the sauna at Langrove Health Club, Parkmill, Gower, spread through the complex, and was attended overnight by ten Mid and West Wales Fire and Rescue Service crews; nearby residents were evacuated. Crews left at 07:18 BST on 15 August. ([Wales Online](https://www.walesonline.co.uk/news/wales-news/fire-tears-through-health-club-34464482), quoting MAWWFRS)

| Field | Value |
|---|---|
| Status | successful |
| Incident type | structure fire |
| Call / attendance | 19:27–06:18 UTC (14–15 Aug 2026) |
| FIRMS | NOAA-20 / `VIIRS_NOAA20_NRT` at **02:13 UTC** 15 Aug |
| Pixel | 51.59103, −4.07489 · FRP 0.32 MW · nominal |
| Offset from site | ~260 m |
| External IDs | `EXT-2026-LANGROVE-HC-MAWWFRS`, `EXT-2026-LANGROVE-HC-NEWS` |
