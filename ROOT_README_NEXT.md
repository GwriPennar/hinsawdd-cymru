# Hinsawdd Cymru

**Data agored, dadansoddiad tryloyw, ffeithiau am hinsawdd Cymru.**

Open and reproducible analysis of public weather, climate and climate-related environmental data for Wales.

Hinsawdd Cymru is a public-facing research repository. Each numbered project asks a specific question, retains source and derived data, documents assumptions, and produces outputs that can be checked independently. New graphics follow the dark-mode-first system in [VISUAL_STYLE.md](VISUAL_STYLE.md).

The repository keeps authoritative published values, independent calculations, provisional results, modelled scenarios and external corroboration clearly separated.

## Project registry

| ID | Project | Status | Main result |
|---|---|---|---|
| [001](projects/001-rolling-temperature/) | Wales August-to-July mean temperature | Provisional, independently revalidated | The 12 months ending July 2026 are robustly the warmest equivalent August-to-July period under every scenario tested. |
| [002](projects/002-temperature-pathways/) | Wales temperature pathways | Stage A statistical baseline | A transparent modern-period regression provides an illustrative comparison baseline, not a physical climate forecast. |
| [003](projects/003-wales-rainfall/) | Wales rainfall and dryness since 1836 | Published historical analysis | July 2026 was exceptionally dry, while the complete August 2025-July 2026 period was slightly wetter than the 1991-2020 reference. |
| [004](projects/004-wales-water-consumption/) | Wales water consumption and data-centre demand | Research baseline v0.1 | Compares Welsh public water supply with transparent modelled data-centre demand scenarios. |
| [005](projects/005-wales-air-quality/) | Wales air quality | Stage A observational baseline | Builds a reference-grade PM2.5 baseline from Welsh AURN monitoring stations before attempting source attribution. |
| [006](projects/006-wildfire-watch/) | Wales Wildfire Watch | **Published first public release, provisional research output** | Reproducibly maps NASA FIRMS VIIRS thermal anomalies over Wales, applies an official Welsh Government boundary, assigns transparent satellite-evidence bands and keeps external wildfire corroboration as a separate auditable layer. |

## Project 006: Wales Wildfire Watch

Project 006 is the first published satellite-observation project in the repository. It ingests public NASA FIRMS near-real-time VIIRS observations from Suomi NPP, NOAA-20 and NOAA-21, retains source provenance, groups repeated nearby observations transparently, and produces scientific Wales maps using an official Welsh Government DataMapWales boundary.

The maps are generated programmatically with **Python, pandas, Matplotlib and Seaborn**. They are code-generated scientific graphics, not generative-image outputs.

### Provisional publication caveat

This is a **first public release** and should be treated as provisional research. NASA FIRMS identifies active-fire and thermal-anomaly pixels; it is not an official Welsh wildfire incident register. A thermal anomaly may be a wildfire, industrial heat or another hot source.

Project 006 therefore keeps two interpretation layers separate:

1. **Satellite evidence**, currently labelled `low`, `plausible` or `strong satellite evidence`, based only on the satellite record.
2. **External corroboration**, using a curated register that prioritises fire and rescue services, Welsh Government, NRW, police and other reliable public sources.

A **known recent wildfire site** does not mean the current satellite signal is a confirmed ongoing fire. Likewise, **no current match found** means only that the current curated public-source register has no matching record. Public incident reporting is incomplete, so absence of a report is not evidence that no fire exists.

The classification thresholds and external-incident register will be refined as more confirmed Welsh wildfires and known non-wildfire heat sources are added. The underlying observations are retained rather than discarded when interpretation is uncertain.

[Read the full Project 006 report and methodology](projects/006-wildfire-watch/).

## Reproducibility

The repository uses a lightweight Reproducible Analytical Pipeline. Projects retain source provenance, generate machine-readable outputs, document evidence boundaries, and run automated validation through GitHub Actions.

Project 006 adds an explicit separation between:

**satellite observation → derived cluster → satellite-evidence category → independent external corroboration**.

That separation is intentional: no single layer is sufficient by itself to establish a confirmed wildfire.

## Sources and licensing

Projects use public datasets from organisations including the Met Office, Welsh Government, NRW, DEFRA UK-AIR and NASA FIRMS. Project 006 uses NASA FIRMS VIIRS thermal-anomaly data, Welsh Government DataMapWales boundary data, and a curated external-incident source register with retained source URLs and statements.

Source data remain subject to their original licences and copyright. Repository analysis code is released under the [MIT License](LICENSE).

## Independence

This is an independent project and is not an official Met Office, Welsh Government, Senedd Cymru, Natural Resources Wales, NASA, DEFRA, UK Government or Welsh fire and rescue service product. Derived results should be described as independent calculations from cited public evidence, not as figures published or endorsed by those organisations.
