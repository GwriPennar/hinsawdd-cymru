# Project 006 figure registry

Canonical map products for Wales Wildfire Watch. Prefer these stable filenames in README and publication links; date-stamped copies are archival siblings created by `stamp_maps.py`.

| ID | Stable filename stem | Script | What it shows | Default output |
|---|---|---|---|---|
| `wales-clusters` | `wales_wildfire_watch_dark` | `scientific_map.py` | Derived thermal-anomaly **clusters** inside the official Communities (Wales) boundary, coloured by satellite-evidence band | `published/figures/` |
| `wales-pixels` | `wales_firms_pixels_dark` | `pixel_map.py` | Individual NASA FIRMS VIIRS **pixels** at reported coordinates inside the official Wales boundary | `published/figures/` |
| `swansea-gower-bbox` | `swansea_gower_watch_bbox_dark` | ad-hoc / local | Swansea–Gower **watch rectangle** on the Wales boundary map | `published/local/swansea-gower/figures/` |
| `swansea-gower-firms` | `swansea_gower_firms_dark` | ad-hoc / local | Swansea–Gower box with local FIRMS hits + Langrove report marker | `published/local/swansea-gower/figures/` |
| `wales-now-pixels` | `wales_now_firms_pixels_dark` | ad-hoc / local | Situational Wales pixel pull (not the publication stem) | `published/local/wales-now/figures/` |

## Formats

Publication stems normally emit:

- widescreen PNG + SVG (`…_dark.png` / `.svg`)
- square PNG + SVG (`…_dark_square.png` / `.svg`)
- date-stamped copies after `stamp_maps.py` (`…_YYYY-MM-DD_HHMMUTC_dark…`)

## Which one to use

- **Situation / social / “where are the hotspots?”** → `wales-pixels`
- **Research publication / ranked candidates** → `wales-clusters`
- **Langrove / Mumbles / Gower local question** → `swansea-gower-firms`
- **Explain the local API box** → `swansea-gower-bbox`

## Rebuild (publication pair)

```bash
export NASA_FIRMS_MAP_KEY="…"
python projects/006-wildfire-watch/build.py --days 2 --bbox uk --output-root projects/006-wildfire-watch/published
python projects/006-wildfire-watch/scientific_map.py --output-root projects/006-wildfire-watch/published
python projects/006-wildfire-watch/pixel_map.py --output-root projects/006-wildfire-watch/published
python projects/006-wildfire-watch/stamp_maps.py --output-root projects/006-wildfire-watch/published
```

Both `wales-clusters` and `wales-pixels` are produced by the daily workflow. Local Swansea/Gower figures remain manual.
