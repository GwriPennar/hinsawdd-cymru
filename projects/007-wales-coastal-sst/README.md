# Project 007 — Wales coastal sea-surface temperature

## Publication status

**Stage 0 — research brief.** No published SST figures yet.

## Question

How have sea-surface temperatures around the Welsh coast been changing in recent years and seasons, and what does the current shelf-sea state look like against a long climatology — including as a public, Wales-focused window while the Pacific El Niño / ENSO cycle evolves?

Project 007 is observational. It does **not** treat El Niño as a direct cause of Welsh coastal SST. ENSO is a **global climate-context** layer; any Wales–ENSO link must be shown empirically or left as open context.

## Why now

- Welsh coastal and shelf seas are a climate and ecology signal in their own right (Irish Sea, Bristol Channel, Cardigan Bay, Celtic Sea approaches).
- Public interest in marine heat and ENSO is high; a reproducible Wales product fills a gap between global SST dashboards and local meaning.
- Fits the Hinsawdd Cymru pattern: open source data → retained provenance → dark-mode scientific graphics → explicit caveats.

## Proposed evidence layers (keep separate)

1. **Satellite foundation SST** (daily L4 analysis) over a Wales coastal / shelf box  
2. **Climatology & anomaly** (e.g. 1991–2020 or product-native climate normal)  
3. **Regional series** (Irish Sea, Cardigan Bay, Bristol Channel / Severn approaches — not one undifferentiated “Wales mean” without saying so)  
4. **Optional ENSO context** (ONI / MEI or equivalent) plotted beside Wales SST — correlation only if computed and documented  
5. **Optional in situ checks** later (tide-gauge / buoy / Cefas where openly available)

## Preferred Stage A data

| Role | Candidate product | Notes |
|---|---|---|
| High-res NRT shelf SST | Copernicus Marine **ODYSSEA** NW Shelf / IBI L4 (`SST_ATL_SST_L4_NRT_OBSERVATIONS_010_025`) | ~0.02°; good coastal Wales / Irish Sea coverage |
| Long climate baseline | Copernicus / Met Office **OSTIA** reprocessed L4 (`SST_GLO_SST_L4_REP_OBSERVATIONS_010_011`) | Daily foundation SST from ~1981; Met Office heritage |
| Operational continuity | OSTIA NRT L4 (`SST_GLO_SST_L4_NRT_OBSERVATIONS_010_001`) | Same family as reprocessed; useful for “now” |
| ENSO context (optional) | NOAA ONI or equivalent open index | Context strip only until a Wales link is tested |

Access: Copernicus Marine Data Store (account + Python `copernicusmarine` or equivalent). Retain raw NetCDF (or extracted CSV) plus SHA-256 provenance under `data/raw/`.

## Working Wales shelf window (draft)

Approximate analysis bbox for Stage A (lon/lat, WGS84):

- west **−6.5°**, south **51.2°**, east **−2.6°**, north **53.6°**

This covers Welsh coasts and adjacent shelf water, including Bristol Channel approaches and the eastern Irish Sea fringe. Exact polygons for named sub-basins come in Stage A.

## Stage plan

| Stage | Deliverable |
|---|---|
| **0** | This brief + source shortlist (current) |
| **A** | Pull ODYSSEA/OSTIA subset; daily mean SST for Wales box; dark time-series + anomaly map; provenance |
| **B** | Sub-basin series (Irish Sea / Cardigan Bay / Bristol Channel); seasonal climatology |
| **C** | Optional ENSO context panel; document any (or no) contemporaneous link |
| **D** | Marine heatwave-day counting with an explicit definition (e.g. Hobday-style) — only after Stage A is solid |

## Caveats (non-negotiable)

- L4 SST is an **analysis**, not a thermometer in the sea. Coastal pixels can be mixed land/sea; mask carefully.
- Foundation SST ≠ skin SST ≠ bathing-water temperature.
- El Niño / La Niña are Pacific phenomena; UK shelf SST is dominated by Atlantic / local processes. Do not headline “El Niño warms Wales” without evidence.
- This is not an official Met Office, Copernicus, NRW or Welsh Government product.

## Visual style

Follow [VISUAL_STYLE.md](../../VISUAL_STYLE.md): dark-mode-first widescreen + square PNG/SVG; cyan/blue for sea temperature; amber/pink only for warm anomalies or extremes that need emphasis.

## Reproduce (when Stage A lands)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
# plus: copernicusmarine / xarray / netCDF4 as required by Stage A
```

Copernicus Marine credentials will be required for live pulls (`COPERNICUSMARINE_SERVICE_USERNAME` / password or the CLI login flow).

## Next action

Stage A: register Copernicus Marine access, lock the Wales bbox and product IDs, extract a first daily SST series and anomaly chart for the Welsh shelf.
