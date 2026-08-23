# Project 007 — sources

Download provenance (URLs, timestamps, checksums) lives under `data/raw/`.

## Sea-surface temperature — Stage B primary

| Product | ID / portal | Role |
|---|---|---|
| Copernicus Marine **ODYSSEA** NW Shelf / IBI L4 SST (NRT) | `SST_ATL_SST_L4_NRT_OBSERVATIONS_010_025` · dataset `IFREMER-ATL-SST-L4-NRT-OBS_FULL_TIME_SERIE` | ~0.02° daily foundation SST for Welsh shelf |
| Retained daily mean | `data/raw/odyssea_wales_shelf_daily_mean.csv` | Wales-box area-mean series |
| Provenance | `data/raw/odyssea_wales_shelf.provenance.json` | Retrieval metadata + checksums |
| Yearly NetCDF cache | `data/raw/odyssea_yearly/` (gitignored) | Local extracts for map climatology |

## Sea-surface temperature — Stage A climate baseline

| Product | Portal | Role |
|---|---|---|
| Met Office **HadISST1** monthly SST | [HadOBS / Met Office](https://www.metoffice.gov.uk/hadobs/hadisst/) | Long 1° monthly analysis (1870–) |
| Retained extract | `data/raw/hadisst_wales_shelf_monthly.csv` | Box-subset ocean cells |

## ENSO context

| Product | Notes |
|---|---|
| NOAA CPC Oceanic Niño Index (ONI) | Public ASCII; Pacific ENSO state only — not Wales causation |
| Retained files | `data/raw/oni.ascii.txt`, `oni.csv`, `oni.provenance.json` |

## Optional / next products

| Product | ID / portal | Role |
|---|---|---|
| OSTIA global L4 SST (reprocessed) | `SST_GLO_SST_L4_REP_OBSERVATIONS_010_011` | Long daily climate baseline (~1981–) for 1991–2020 daily normals |
| OSTIA global L4 SST (NRT) | `SST_GLO_SST_L4_NRT_OBSERVATIONS_010_001` | Near-real-time OSTIA family |
| NOAA OISST v2.1 daily 0.25° | NOAA / AWS / ERDDAP | Open daily alternative |

Portals:

- https://data.marine.copernicus.eu/
- https://www.metoffice.gov.uk/hadobs/hadisst/
- https://www.cpc.ncep.noaa.gov/data/indices/
- https://ghrsst-pp.metoffice.gov.uk/ostia-website/

## Licensing

Met Office HadOBS, NOAA CPC and Copernicus Marine products remain under their original licences and citation requirements. Project 007 publishes independent derived charts and tables from cited public evidence; it does not redistribute whole catalogues.
