# Project 007 figure registry

Canonical charts for Wales coastal / NW Europe sea-surface temperature. Prefer these stable filenames in README, GitHub and the HTML snapshot.

| ID | Stable filename | What you are looking at | Geographic window | How to read it |
|---|---|---|---|---|
| `nw-europe-sst` | `nw_europe_sst_snapshot_dark.png` | **Latest-day foundation SST** on the ~0.02° ODYSSEA grid | lon −12°…3°, lat 49°…61° (British Isles + surrounding shelf seas) | Colour = absolute sea temperature (°C). Dark gaps = land / no ocean mask. **Dashed box** = Wales shelf headline area used for the time series. |
| `nw-europe-anomaly` | `nw_europe_sst_anomaly_snapshot_dark.png` | **Same day, anomaly vs climatology** | Same regional window | Red = warmer than the 2019–2023 average for this calendar day; blue = cooler. Shows whether the whole NE Atlantic shelf is unusually warm, not just Wales. |
| `wales-history` | `wales_shelf_sst_daily_history_dark.png` | **Wales shelf area-mean time series** | Wales box only (lon −6.5°…−2.6°, lat 51.2°…53.6°) | Top: daily SST (cyan) vs 2019–2023 day-of-year normal (blue). Bottom: anomaly bars. One number summarising Welsh shelf conditions. |
| `wales-anomaly-map` | `wales_shelf_sst_daily_anomaly_map_dark.png` | **Shelf-scale anomaly detail** | Wales box at full grid resolution | Zoomed view of the dashed box in the regional maps. Use when you need local shelf patterns (e.g. Bristol Channel vs Cardigan Bay tendency). |
| `enso-context` | `wales_shelf_sst_daily_enso_context_dark.png` | **Pacific ENSO context strip** | Wales anomaly (top) + NOAA ONI (bottom) | ONI is **Pacific-only context**. It does **not** mean El Niño is driving Welsh SST. |
| `hadisst-history` | `wales_shelf_sst_history_dark.png` | Stage A monthly climate baseline | Wales box, 1870–present | Long-run monthly SST vs 1991–2020 normal (HadISST 1°). |
| `hadisst-anomaly` | `wales_shelf_sst_anomaly_map_dark.png` | Stage A latest monthly anomaly map | Wales box | Coarser (1°) monthly context. |

Square variants (`*_square.png`) use the same data with a 1:1 layout for social / thumbnail use.

## What this data is (and is not)

| | |
|---|---|
| **Is** | Satellite-based **foundation SST analysis** (Copernicus ODYSSEA L4, ~0.02°). Daily field centred **00:00 UTC**. Gap-filled grid over open ocean. |
| **Is not** | A beach or harbour thermometer reading. Not a real-time single satellite snapshot. Not an official Met Office or Welsh Government product. |
| **Anomaly baseline (Stage B)** | **2019–2023** same calendar day (ODYSSEA archive limit), not 1991–2020. |
| **Best refresh time** | After **12:30 UTC** daily (Copernicus target delivery ~12:00 UTC). |

## HTML snapshot

Browse all current figures with headlines and explainers:

- [`published/snapshot/index.html`](published/snapshot/index.html)

## Rebuild

```bash
copernicusmarine login   # one-time
python projects/007-wales-coastal-sst/run_stage_b.py
```
