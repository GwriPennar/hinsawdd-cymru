# Project 006 — current situation (16 August 2026)

This note explains **where Wales Wildfire Watch stands right now**: what the latest published maps show, what is *not* confirmed, and how the overnight FIRMS watch behaved.

It is a situational readout, not a fire-service bulletin. Satellite thermal anomalies are **not** automatically wildfires.

---

## Snapshot in one paragraph

The latest **successful publication** is **16 August 2026 14:03 UTC** (date-stamped maps `2026-08-16_1403UTC`). In that two-day UK pull, the Wales watch window has **307** VIIRS detections and **13** candidate clusters inside the official Communities (Wales) boundary. The newest observation in the published snapshot is **16 August 2026 12:29 UTC**. The standout ranked cluster is **Llangynidr** (236 detections, multi-satellite, peak FRP ~16.9 MW, evidence band **plausible**). Overnight FIRMS ping watches timed out twice before that refresh; NASA global NRT lag of ~1–3 hours (and passes with no new UK hotspots) explained the quiet periods.

---

## Latest publication numbers

| Field | Value |
|---|---|
| Data snapshot | **2026-08-16 14:03 UTC** |
| Latest satellite observation | **2026-08-16 12:29 UTC** |
| Wales-window detections | **307** |
| Candidate clusters (Wales boundary) | **13** |
| Evidence bands in this set | **plausible** (9), **low** (4) — no **strong** this refresh |
| Top candidate by detections | **Llangynidr** (236 dets; N + N20 + N21; last hit 01:56 UTC) |
| Newest multi-sat cluster | **Talley** (9 dets; last hit 03:36 UTC) |
| Gower local window | Still quiet relative to Wales; Langrove structure-fire correlation remains a separate local record |

Stable map files (also date-stamped):

- Scientific map with location list: `published/figures/wales_wildfire_watch_dark.png`
- Pixel map: `published/figures/wales_firms_pixels_dark.png`

---

## What happened with the FIRMS watcher

Local operator tooling (`firms_ping.py`) polled NASA FIRMS every minute and only triggered a full `run_all` when UK or Gower **latest observation time** moved past a baseline.

| Watch window | Result |
|---|---|
| ~02:22–04:22 UTC 16 Aug | **Timeout** — baseline stuck on 15 Aug 13:46 UTC |
| ~11:35–13:35 UTC 16 Aug | **Timeout** — baseline stuck on 16 Aug 03:36 UTC |
| Later afternoon refresh | Publication succeeded at **14:03 UTC** with latest obs **12:29 UTC** |

That pattern matches known FIRMS behaviour for Wales:

1. **Global VIIRS NRT latency** is typically **within ~3 hours** of observation (best effort). Ultra/real-time (minutes) is mainly US/Canada direct readout — not this UK API path.
2. **Latest-obs only advances when a newer thermal anomaly is published.** A geometrically good overpass with no UK hotspots leaves the timestamp unchanged.
3. A **pass calendar** (`pass_calendar.py` / waiting room) was added so quiet periods can be read as *no pass yet* vs *pass already happened — waiting on NRT* vs *clean pass / no new fires*.

---

## How to read the maps today

- **Llangynidr** is the high-volume / top-ranked cluster on the locations panel — repeated multi-satellite signal, still **plausible**, not externally confirmed in this publication.
- **Talley** is the freshest multi-satellite cluster after the overnight NOAA-20 window.
- Pixel-level FIRMS **high** confidence remains rare in this window (isolated pixels ≠ ranked “strong” evidence band).
- External corroboration (news / FRS reports) is a **separate** layer. A nearby known incident does not prove the current satellite cluster is the same event.

---

## Operator tools added in this update

| Script | Purpose |
|---|---|
| `firms_ping.py` | Poll FIRMS until latest obs moves; optional `--run-all --open` |
| `pass_calendar.py` | TLE-based Wales/Gower VIIRS culmination calendar + status line |
| `waiting_room.py` | Dark local HTML status page (FIRMS × passes × ~3h NRT windows) |
| `run_all.py` | Situational full refresh bundle (Wales + Gower + wales-now) |
| `local_watch.py` | Swansea–Gower rolling local window |

Local HTML/JSON for the waiting room lives under `published/local/pass-calendar/` (situational; not the canonical GitHub publication stem).

---

## Reproduce the published refresh

```bash
cd /Users/gwri/Documents/hinsawdd-cymru   # or your clone root
source .venv/bin/activate
export NASA_FIRMS_MAP_KEY="$(tr -d '\n\r ' < secrets/nasa\ firms.txt)"

# Canonical publication path (simplified)
python projects/006-wildfire-watch/build.py --days 2 --bbox uk --output-root projects/006-wildfire-watch/published
python projects/006-wildfire-watch/scientific_map.py --output-root projects/006-wildfire-watch/published
python projects/006-wildfire-watch/pixel_map.py --output-root projects/006-wildfire-watch/published
python projects/006-wildfire-watch/stamp_maps.py --output-root projects/006-wildfire-watch/published
# … location links, corroboration, history, publication_status …

# Or situational all-in-one:
python projects/006-wildfire-watch/run_all.py --open
```

Pass calendar / waiting room (needs `skyfield` + network for CelesTrak TLEs):

```bash
python projects/006-wildfire-watch/pass_calendar.py --figure
python projects/006-wildfire-watch/waiting_room.py --open
```

---

## Caveats (unchanged)

- Not an official NASA, Welsh Government, NRW or fire-and-rescue product.
- NRT can be revised; later Standard Processing may disagree.
- 375 m VIIRS is product resolution, not GPS pin-point accuracy.
- See [METHODOLOGY.md](METHODOLOGY.md), [SOURCES.md](SOURCES.md), [CORRELATIONS.md](CORRELATIONS.md), [FIGURES.md](FIGURES.md).
