# Hinsawdd Cymru

**Data agored, dadansoddiad tryloyw, ffeithiau am hinsawdd Cymru.**

Open and reproducible analysis of public weather, climate and climate-related environmental data for Wales.

Hinsawdd Cymru is a public-facing research repository. Each numbered project asks a specific question, retains source and derived data, documents assumptions, and produces outputs that can be checked independently. New graphics follow the dark-mode-first system documented in [VISUAL_STYLE.md](VISUAL_STYLE.md).

## Project registry

| ID | Project | Status | Main result |
|---|---|---|---|
| [001](projects/001-rolling-temperature/) | Wales August-to-July mean temperature | Provisional, independently revalidated | Warmest equivalent August-to-July period under every scenario tested. |
| [002](projects/002-temperature-pathways/) | Wales temperature pathways | Stage A statistical baseline | Transparent statistical comparison baseline; not a physical climate forecast. |
| [003](projects/003-wales-rainfall/) | Wales rainfall and dryness since 1836 | Published historical analysis | July 2026 was exceptionally dry; the complete August 2025–July 2026 period was slightly wetter than the 1991–2020 reference. |
| [004](projects/004-wales-water-consumption/) | Wales water consumption and data-centre demand | Research baseline v0.1 | Transparent comparison of public water supply and modelled data-centre demand. |
| [005](projects/005-wales-air-quality/) | Wales air quality | Stage A observational baseline | Reference-grade PM2.5 baseline from Welsh AURN monitoring stations. |
| [006](projects/006-wildfire-watch/) | Wales Wildfire Watch | **Published, provisional research output** | Reproducible NASA FIRMS VIIRS thermal-anomaly mapping, official Wales boundary, historical record and external corroboration. |

## Project 006 — Wales Wildfire Watch

Project 006 uses public NASA FIRMS near-real-time VIIRS observations from Suomi NPP, NOAA-20 and NOAA-21 and the official Welsh Government DataMapWales Communities (Wales) boundary.

The map is generated programmatically with **Python, pandas, Matplotlib and Seaborn**. It is a code-generated scientific graphic, not a generative-image output.

### Latest published map

<a href="projects/006-wildfire-watch/published/figures/wales_wildfire_watch_dark.png"><img src="projects/006-wildfire-watch/published/figures/wales_wildfire_watch_dark.png" alt="Latest Wales Wildfire Watch scientific map" width="100%"></a>

<p align="center"><a href="projects/006-wildfire-watch/published/figures/wales_wildfire_watch_dark_square.png"><img src="projects/006-wildfire-watch/published/figures/wales_wildfire_watch_dark_square.png" alt="Latest square Wales Wildfire Watch map" width="72%"></a></p>

The current published two-day run (snapshot **21 August 2026 16:34 UTC**, latest obs **13:12 UTC**) contains **19 VIIRS detections in the Wales watch window** and **4 derived candidate clusters inside the official Wales boundary**. These are thermal anomalies, **not a confirmed wildfire count**. The top-ranked cluster this refresh is **Glascwm** (plausible, multi-satellite). Swansea/Gower 24h watch is quiet (**0** detections).

Project 006 maintains a cumulative historical record under `data/history/`. A daily GitHub Actions workflow refreshes the latest data, rebuilds the maps, adds OpenStreetMap and Google Maps links, runs external corroboration and commits changed outputs back to `main`. Local operator tools (`firms_ping`, pass calendar, waiting room) help separate satellite geometry from FIRMS NRT lag.

The project keeps these evidence layers separate:

**satellite observation → derived cluster → satellite-evidence category → independent external corroboration**

[Current situation (21 Aug 2026)](projects/006-wildfire-watch/CURRENT_SITUATION.md) · [Full Project 006 report, caveats and methodology](projects/006-wildfire-watch/)

## Reproducibility

The repository uses a lightweight Reproducible Analytical Pipeline: source provenance, machine-readable derived outputs, documented assumptions and GitHub Actions validation.

## Sources and licensing

Projects use public datasets from organisations including the Met Office, Welsh Government, NRW, DEFRA UK-AIR and NASA FIRMS. Source data remain subject to their original licences and copyright. Repository analysis code is released under the [MIT License](LICENSE).

## Independence

This is an independent project and is not an official Met Office, Welsh Government, Senedd Cymru, Natural Resources Wales, NASA, DEFRA, UK Government or Welsh fire and rescue service product. Derived results should be described as independent calculations from cited public evidence, not as figures published or endorsed by those organisations.
