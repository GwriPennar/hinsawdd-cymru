# Project 007 — sources

Stage A uses open HadISST + ONI. Download provenance (URLs, timestamps, checksums) lives under `data/raw/`.

## Sea-surface temperature (Stage A primary)

| Product | Portal | Role |
|---|---|---|
| Met Office **HadISST1** monthly SST | [HadOBS / Met Office](https://www.metoffice.gov.uk/hadobs/hadisst/) | Long 1° monthly analysis; Wales-shelf extract for Stage A |
| Retained extract | `data/raw/hadisst_wales_shelf_monthly.csv` | Box-subset ocean cells; see matching `.provenance.json` |

## ENSO context (Stage A)

| Product | Notes |
|---|---|
| NOAA CPC Oceanic Niño Index (ONI) | Public ASCII; Pacific ENSO state only — not Wales causation |
| Retained files | `data/raw/oni.ascii.txt`, `oni.csv`, `oni.provenance.json` |

## Higher-resolution follow-on (not Stage A)

| Product | ID / portal | Role |
|---|---|---|
| ODYSSEA NW Shelf / IBI L4 SST (NRT) | Copernicus Marine `SST_ATL_SST_L4_NRT_OBSERVATIONS_010_025` | ~0.02° daily foundation SST for Welsh shelf / Irish Sea |
| OSTIA global L4 SST (reprocessed) | Copernicus Marine `SST_GLO_SST_L4_REP_OBSERVATIONS_010_011` | Long daily climate baseline (~1981–) |
| OSTIA global L4 SST (NRT) | Copernicus Marine `SST_GLO_SST_L4_NRT_OBSERVATIONS_010_001` | Near-real-time OSTIA family |
| NOAA OISST v2.1 daily 0.25° | NOAA / AWS / ERDDAP | Open daily alternative when pull path is reliable |

Portals:

- https://www.metoffice.gov.uk/hadobs/hadisst/
- https://www.cpc.ncep.noaa.gov/data/indices/
- https://data.marine.copernicus.eu/
- https://ghrsst-pp.metoffice.gov.uk/ostia-website/

## Licensing

Met Office HadOBS, NOAA CPC and Copernicus Marine products remain under their original licences and citation requirements. Project 007 publishes independent derived charts and tables from cited public evidence; it does not redistribute whole catalogues.
