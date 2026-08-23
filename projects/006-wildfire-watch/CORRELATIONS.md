# Project 006 successful correlations

Registry of cases where a NASA FIRMS thermal anomaly was later tied to an independently reported incident.

Machine-readable table: [`data/reference/successful_correlations.csv`](data/reference/successful_correlations.csv)

External incident sources remain in [`data/reference/external_wildfire_incidents.csv`](data/reference/external_wildfire_incidents.csv). That file name is historical; rows may include structure fires when they corroborate a thermal anomaly.

## Evidence rule

A successful correlation means:

1. a retained FIRMS detection (source, time, lat/lon, FRP/confidence);
2. an independent external report (preferably fire service);
3. close spatial match and overlapping time window;
4. explicit incident type (`structure_fire`, `wildfire`, etc.).

It does **not** reclassify the FIRMS pixel as a confirmed wildfire.

**Candidate** rows may be recorded when an independent report and a FIRMS detection share a plausible area and time window, but spatial offset is larger than a site match (e.g. locality-level observer attribution a few kilometres from the pixel) or the external source is not yet fire-service grade. Candidates are not successful correlations.

**Likely industrial** rows flag thermal anomalies that sit on or beside a known active industrial heat source (e.g. cement kiln). They are operator assessments, not fire-service confirmations, and they do **not** reclassify the anomaly as a wildfire. Persistent industrial sites are listed in [`data/reference/known_industrial_heat_sources.csv`](data/reference/known_industrial_heat_sources.csv).

## Current entries

### CORR-2026-LANGROVE-HC-001 — Langrove Health Club, Parkmill

**News (brief):** On the evening of 14 August 2026 a fire started in the sauna at Langrove Health Club, Parkmill, Gower, spread through the complex, and was attended overnight by ten Mid and West Wales Fire and Rescue Service crews; nearby residents were evacuated. Crews left at 07:18 BST on 15 August. ([Wales Online](https://www.walesonline.co.uk/news/wales-news/fire-tears-through-health-club-34464482), quoting MAWWFRS)

| Field | Value |
|---|---|
| Status | successful |
| Incident type | structure fire |
| Call / attendance | 19:27–06:18 UTC (14–15 Aug 2026) |
| FIRMS | NOAA-20 / `VIIRS_NOAA20_NRT` at **02:13 UTC** 15 Aug |
| Pixel | 51.59103, −4.07489 · FRP 0.32 MW · nominal |
| Offset from site | ~260 m |
| External IDs | `EXT-2026-LANGROVE-HC-MAWWFRS`, `EXT-2026-LANGROVE-HC-NEWS` |

### CORR-2026-GORSEINON-JAYPLAS-001 — Jayplas / Gorseinon (candidate)

**Report (brief):** On the evening of 15 August 2026, during a west-Swansea smoke episode, a community report attributed activity to the **Jayplas** plastics recycling facility on Heol y Mynydd, Gorseinon (former Toyoda Gosei site). Same-afternoon Swansea/Gower FIRMS watch found a two-pixel VIIRS cluster near **Bryn Bach Road / Brynbach Uchaf Farm**, about **4.3 km** north-east of the factory — close enough for a locality-level “Gorseinon / Jayplas” observer call, not a site pin.

| Field | Value |
|---|---|
| Status | **candidate** |
| Incident type | community smoke report |
| Report pin | Jayplas, 51.67813, −4.03408 |
| FIRMS | NOAA-20 (peak) + SNPP · **13:23–13:44 UTC** 15 Aug · cluster `HC-TA-20260815-82E40C8` |
| Pixel / cluster | 51.71187, −4.00436 · peak FRP 6.99 MW · nominal |
| Offset from report | ~4.3 km |
| External IDs | `EXT-2026-GORSEINON-JAYPLAS-COMMUNITY` |

### CORR-2026-RHOOSE-TARMAC-001 — Tarmac Aberthaw / Rhoose (likely industrial)

**Assessment (brief):** The **22 August 2026** Wales candidate labelled **Rhoose** (`HC-TA-20260822-77E3817`) is a weak multi-satellite night cluster (~02:28–03:23 UTC; peak FRP ~1.64 MW) whose centroid sits ~280 m from the **active Tarmac Aberthaw Cement Works** at East Aberthaw. Cement kilns routinely produce VIIRS industrial heat. The neighbouring former Aberthaw Power Station is decommissioned (2020) and is a poorer explanation for ongoing process heat.

| Field | Value |
|---|---|
| Status | **likely_industrial** |
| Incident type | industrial heat (cement works) |
| Site pin | Tarmac Aberthaw, 51.39696, −3.39147 (`IND-2026-TARMAC-ABERTHAW`) |
| FIRMS cluster | `HC-TA-20260822-77E3817` · 51.39849, −3.39463 |
| Offset from works | ~280 m |
| Registry | [`known_industrial_heat_sources.csv`](data/reference/known_industrial_heat_sources.csv) |

### CORR-2026-ANGLE-MILFORD-001 — Angle / Milford Haven (likely industrial)

**Assessment (brief):** The **Angle** Wales candidate (`HC-TA-20260822-BE1D844`) is a weak multi-satellite **night** cluster on 22 August, but the same pin has been lighting up repeatedly since mid-June (~181 hits / ~44 days nearby; almost all night; typical FRP ~1–2 MW). That pattern fits **persistent industrial heat / flaring** in the Milford Haven strip (Valero, LNG terminals, Pembroke Power), not a spreading wildfire. Keeping it visible is useful: we can see the recurring anomaly, and a major landscape fire here would be expected to look different (stronger FRP, day+night, growth away from the usual footprint).

| Field | Value |
|---|---|
| Status | **likely_industrial** |
| Incident type | industrial heat (oil / gas / power complex) |
| Screening pin | 51.68434, −5.02983 (`IND-2026-MILFORD-HAVEN-ANGLE`) |
| FIRMS cluster | `HC-TA-20260822-BE1D844` · Angle |
| History cue | recurring night hits since mid-June 2026 |
| Registry | [`known_industrial_heat_sources.csv`](data/reference/known_industrial_heat_sources.csv) |
