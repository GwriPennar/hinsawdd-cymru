# Project 007 — methodology

## Stage B (ODYSSEA daily)

### Question answered

How has area-mean foundation SST over a Wales coastal / shelf box evolved day-by-day since the ODYSSEA NRT archive began, relative to a multi-year day-of-year climatology, and what does the latest day look like on the ~0.02° grid — with Pacific ONI as ENSO context only?

### Data

| Layer | Product | Use |
|---|---|---|
| SST | Copernicus Marine **ODYSSEA** L4 daily (`SST_ATL_SST_L4_NRT_OBSERVATIONS_010_025`) | Subset to Wales shelf bbox; ocean via GHRSST `mask == 1`; Kelvin → °C |
| ENSO context | NOAA CPC **ONI** | Separate context panel — not a Wales causal driver |

Access: free Copernicus Marine account + `copernicusmarine login` (credentials under `~/.copernicusmarine`).

### Wales shelf window

WGS84 bbox: lon **−6.5…−2.6**, lat **51.2…53.6**. Daily area-mean SST is cosine-latitude weighted over ocean cells.

### NW Europe snapshot window

WGS84 bbox: lon **−12…3**, lat **49…61** — Ireland, Great Britain, Isle of Man, and surrounding shelf seas. Snapshot maps use the native ~0.02° ODYSSEA grid at full PNG resolution; a dashed box marks the Wales shelf headline area.

### Update timing

Each daily field is a **foundation SST analysis for calendar day D centred on 00:00 UTC** (not a single satellite overpass). Copernicus target delivery is **~12:00 UTC**; run the pipeline after **12:30 UTC** for the most complete latest day.

### Climatology and anomaly

- Reference: **2019–2023** day-of-year (month-day) means from ODYSSEA (archive starts ~2018; not a 1991–2020 normal).
- Anomaly (°C) = daily box mean − DOY climatology.
- Latest anomaly map: same calendar day averaged over clim years, subtracted from the latest day grid.

### Outputs

- `data/derived/wales_shelf_sst_daily.csv`
- `data/derived/wales_shelf_sst_daily_anomaly_grid_latest.csv`
- `data/derived/summary_daily.json`
- `data/derived/nw_europe_sst_snapshot_grid_latest.csv`
- `data/derived/nw_europe_sst_anomaly_grid_latest.csv`
- `published/snapshot/index.html`
- Dark widescreen + square PNG under `figures/wales_shelf_sst_daily_*` and `figures/nw_europe_*`

---

## Stage A (HadISST monthly)

### Question answered

How has area-mean SST over the same Wales shelf box changed on monthly timescales relative to a **1991–2020** climatology?

### Data

| Layer | Product | Use |
|---|---|---|
| SST | Met Office **HadISST1** monthly, 1° | Open HadOBS NetCDF; Wales-shelf extract |
| ENSO context | NOAA CPC **ONI** | Context panel only |

### Climatology

- **1991–2020** calendar-month means; anomaly = month mean − clim for that month.

### Outputs

- `data/derived/wales_shelf_sst_monthly.csv`, anomaly grid, `summary.json`
- Dark charts `figures/wales_shelf_sst_*` (without `_daily_`)

---

## Explicit non-claims

- L4 SST is an analysis, not in-situ bathing temperature.
- ONI describes the equatorial Pacific; Project 007 does **not** claim El Niño → Wales SST causation.
- Stage B DOY clim is short (2019–2023); Stage A provides the long monthly climate baseline.
- Named sub-basins remain future work.
