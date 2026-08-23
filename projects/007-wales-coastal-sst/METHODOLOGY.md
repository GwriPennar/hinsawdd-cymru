# Project 007 — methodology (Stage A)

## Question answered

How has area-mean sea-surface temperature over a Wales coastal / shelf box changed relative to a 1991–2020 climatology, and what does the latest month look like on the coarse grid — with Pacific ONI shown only as global ENSO context?

## Data

| Layer | Product | Use |
|---|---|---|
| SST | Met Office **HadISST1** monthly, 1° | Open HadOBS NetCDF (`.nc.gz`); subset to Wales shelf bbox; land/ice masked via HadISST missing values |
| ENSO context | NOAA CPC **ONI** | Open ASCII; plotted as a separate context panel — not used as a Wales causal driver |

Copernicus ODYSSEA / OSTIA and NOAA OISST daily remain documented upgrades for Stage B+ when credentials or a reliable daily pull path are available. Stage A deliberately uses HadISST so the pipeline runs without Copernicus Marine login.

## Wales shelf window

WGS84 bbox: lon **−6.5…−2.6**, lat **51.2…53.6**. Area-mean SST is the unweighted mean of ocean cells in that box for each month.

## Climatology and anomaly

- Reference period: **1991–2020** calendar-month means (month-of-year climatology).
- Anomaly (°C) = monthly box mean − climatology for that calendar month.
- Latest anomaly map: same month-of-year climatology applied cell-wise on the 1° extract for the most recent HadISST month.

## Outputs

- `data/derived/wales_shelf_sst_monthly.csv` — monthly box-mean SST and anomaly
- `data/derived/wales_shelf_sst_anomaly_grid_latest.csv` — latest-month cell anomalies
- `data/derived/summary.json` — headline numbers and provenance pointers
- Dark widescreen + square PNG/SVG charts under `figures/`

## Explicit non-claims

- HadISST is a reconstructed analysis, not in-situ coastal bathing temperature.
- ONI describes the equatorial Pacific; this Stage A does **not** claim El Niño → Wales SST causation.
- Coarse 1° cells mix coastal and shelf water; named sub-basins are Stage B.
