# Project 007 — Wales coastal sea-surface temperature

## Publication status

**Stage B published.** Copernicus Marine **ODYSSEA** daily (~0.02°) Wales-shelf series and anomaly maps, alongside Stage A HadISST monthly climate baseline.

## Question

How have sea-surface temperatures around the Welsh coast been changing against a climatology, and what does the current shelf-sea state look like — including as a public Wales window while the Pacific ENSO cycle evolves?

Project 007 is observational. It does **not** treat El Niño as a direct cause of Welsh coastal SST. ENSO is a **global climate-context** layer only.

## Stage B headline (ODYSSEA daily)

Latest day **2026-08-21**: shelf-box SST **17.5 °C**, anomaly **+1.19 °C** vs 2019–2023 day-of-year; trailing 30-day mean anomaly **+1.39 °C**. Latest ONI (MJJ 2026): **+1.39** (Pacific context only).

### Daily history

<a href="figures/wales_shelf_sst_daily_history_dark.png"><img src="figures/wales_shelf_sst_daily_history_dark.png" alt="Wales shelf ODYSSEA daily SST history" width="100%"></a>

### Latest daily anomaly map

<a href="figures/wales_shelf_sst_daily_anomaly_map_dark.png"><img src="figures/wales_shelf_sst_daily_anomaly_map_dark.png" alt="Wales shelf ODYSSEA latest daily anomaly map" width="100%"></a>

### ENSO context (daily)

<a href="figures/wales_shelf_sst_daily_enso_context_dark.png"><img src="figures/wales_shelf_sst_daily_enso_context_dark.png" alt="Wales shelf daily SST anomaly with NOAA ONI context" width="100%"></a>

## What Stage B built

- Copernicus Marine **ODYSSEA** L4 daily foundation SST (`SST_ATL_SST_L4_NRT_OBSERVATIONS_010_025`) for bbox `lon −6.5…−2.6`, `lat 51.2…53.6`
- Area-mean daily series **2018-01-01 → present** with **2019–2023** day-of-year climatology and anomaly
- Latest-day anomaly map on the ~0.02° grid
- NOAA **ONI** context panel (unchanged role: Pacific context only)
- Pipeline: `fetch_odyssea.py` → `analysis_daily.py` → `figures_daily.py` via `run_stage_b.py`

## Stage A (HadISST monthly baseline)

Long climate baseline remains Met Office **HadISST1** monthly (1870–present, 1991–2020 month-of-year clim). See charts under `figures/wales_shelf_sst_history_dark.png` and [METHODOLOGY.md](METHODOLOGY.md).

Latest HadISST month (**2026-06**): shelf-box SST **14.5 °C**, anomaly **+1.07 °C** vs 1991–2020.

## Caveats

- ODYSSEA and HadISST are **analyses**, not coastal bathing thermometers.
- Stage B anomalies use **2019–2023** ODYSSEA day-of-year normals (product archive starts ~2018), not 1991–2020.
- ENSO is Pacific context only — do not headline “El Niño warms Wales”.
- Named sub-basins (Irish Sea / Cardigan Bay / Bristol Channel) remain a later step.
- Not an official Met Office, Copernicus, NRW or Welsh Government product.

## Reproduce

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[sst,dev]"
# one-time Copernicus login after free registration:
copernicusmarine login
python projects/007-wales-coastal-sst/run_stage_b.py
# or reuse retained daily CSV / yearly cache:
python projects/007-wales-coastal-sst/run_stage_b.py --skip-fetch
# Stage A (HadISST) still available:
python projects/007-wales-coastal-sst/run_stage_a.py --skip-fetch
pytest -q projects/007-wales-coastal-sst/tests
```

Bulky NetCDF extracts (`data/raw/odyssea_yearly/`, full HadISST `.nc.gz`) are gitignored; derived CSVs, provenance and figures are retained.

## Stage plan

| Stage | Deliverable |
|---|---|
| **0** | Research brief + source shortlist |
| **A** | HadISST monthly Wales-box series + anomaly map + ONI context |
| **B** | ODYSSEA daily Wales-box series + anomaly map + ONI context (current) |
| **C** | Documented Wales–ENSO empirical comparison (or explicit null); optional sub-basins |
| **D** | Marine heatwave-day counting with an explicit definition |

## Docs

- [METHODOLOGY.md](METHODOLOGY.md)
- [SOURCES.md](SOURCES.md)
