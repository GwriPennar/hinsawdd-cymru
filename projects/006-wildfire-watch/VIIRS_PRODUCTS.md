# VIIRS / JPSS product catalog (Project 006)

Suomi NPP, NOAA-20, and NOAA-21 carry the same core instrument suite. Project 006 already uses **FIRMS VIIRS active-fire CSV**. This catalog explains the wider browse layers we snapshot via NASA **GIBS**, and what full science data would mean later.

## Instruments on the three birds

| Instrument | What it measures | In Project 006 today |
|---|---|---|
| **VIIRS** | Imagery, fires, aerosols, surface temperature, night lights | FIRMS hotspots + GIBS browse snapshots |
| **ATMS** | Microwave temperature / moisture soundings | Not pulled (science granules) |
| **CrIS** | Infrared atmospheric soundings | Not pulled (science granules) |
| **OMPS** | Ozone / some volcanic SO₂ / aerosol profiles | Not pulled (science granules) |
| **CERES** (NPP, NOAA-20) / **Libera** (NOAA-21) | Earth radiation budget | Not pulled (science granules) |

## GIBS browse vs full science granules

- **GIBS WMS / Worldview-style browse** — daily rendered images for a bbox. Fast, no Earthdata login, good for “what does this product look like over Wales?”. Pulled by `viirs_snapshot.py`.
- **Full Level-1/2 granules** — HDF5/NetCDF science files from LAADS / NOAA CLASS. Multi‑GB, need Earthdata auth, needed for quantitative ATMS/CrIS/OMPS analysis. **Out of v1.**

FIRMS area CSV remains the hotspot table pipeline (`build.py` / `local_watch.py`). GIBS thermal-anomaly layers are a visual complement only.

## Simplified default outputs (after feedback)

Default run is **Wales + NOAA-20 only**, five products (≈5 explained figures + review page):

| Theme | Why kept |
|---|---|
| True colour | Smoke / landscape context |
| AOD Deep Blue | Haze / smoke thickness (with Wales outlines) |
| Thermal anomalies | Browse complement to FIRMS |
| Land surface temp (day) | Heat context |
| False colour (burn / vegetation) | Burn/vegetation contrast vs true colour |

**Dropped by default**

- Day/Night Band (noisy / unhelpful daytime)
- Per-satellite triples (use `--satellites all` only when comparing birds)
- Swansea–Gower crop (too blurry at GIBS zoom; use `--also-gower-crop` only if needed)

Figures include **Communities (Wales) outlines**, larger caption text, and higher WMS resolution (`--max-edge 2000`).

## How to run

```bash
# Default simplified set
python projects/006-wildfire-watch/viirs_snapshot.py --date 2026-08-15 --bbox wales

# All three birds (larger review set)
python projects/006-wildfire-watch/viirs_snapshot.py --date 2026-08-15 --bbox wales --satellites all
```

Outputs land under `published/local/viirs-snapshot/<stamp>/`:

- `raw/` — plain GIBS frames
- `figures/viirs_{area}_{SAT}_{theme}_dark.png` — **separate explained figures**
- `figures/EXPLAINERS.md` — index
- `review.html` — feedback UI → save `feedback.json` in the stamp folder
- `figures/viirs_browse_contact_dark.png` — overview grid
