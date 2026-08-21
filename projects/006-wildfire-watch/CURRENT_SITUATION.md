# Project 006 — current situation (21 August 2026)

This note explains **where Wales Wildfire Watch stands right now**: what the latest published maps show, what is *not* confirmed, and how quiet the Gower/Swansea window is.

It is a situational readout, not a fire-service bulletin. Satellite thermal anomalies are **not** automatically wildfires.

---

## Snapshot in one paragraph

The latest **successful publication** is **21 August 2026 16:34 UTC** (date-stamped maps `2026-08-21_1634UTC`). In that two-day UK pull, the Wales watch window has **19** VIIRS detections and **4** candidate clusters inside the official Communities (Wales) boundary. The newest observation in the published snapshot is **21 August 2026 13:12 UTC**. Activity is **much quieter** than the 16 August Llangynidr spike. The top ranked cluster is **Glascwm** (7 detections, multi-satellite, peak FRP ~5.6 MW, evidence band **plausible**). The **Swansea/Gower 24h watch is quiet** — **0** detections.

---

## Latest publication numbers

| Field | Value |
|---|---|
| Data snapshot | **2026-08-21 16:34 UTC** |
| Latest satellite observation | **2026-08-21 13:12 UTC** |
| Wales-window detections | **19** |
| Candidate clusters (Wales boundary) | **4** |
| Evidence bands in this set | **plausible** (4) — no **strong** / **low** this refresh |
| Top candidate by detections | **Glascwm** (7 dets; N + N20 + N21; last hit 20 Aug 13:50 UTC) |
| Other clusters | Pontlottyn/Abertysswg area; two **Angle** clusters (newer last hit **21 Aug 03:42 UTC**) |
| Gower / Swansea 24h watch | **0 detections** — quiet |

Stable map files (also date-stamped):

- Scientific map with location list: `published/figures/wales_wildfire_watch_dark.png`
- Pixel map: `published/figures/wales_firms_pixels_dark.png`
- Gower local: `published/local/swansea-gower/figures/swansea_gower_firms_dark.png`
- All-in-one HTML: `published/local/refresh/latest/index.html`

---

## Compared with 16 August

| | 16 Aug 14:03 UTC | 21 Aug 16:34 UTC |
|---|---|---|
| Wales detections | 307 | **19** |
| Candidate clusters | 13 | **4** |
| Standout | Llangynidr (236 dets) | Glascwm (7 dets) |
| Gower 24h | Quiet relative to Wales | **Quiet (0)** |

The 16 August Llangynidr episode remains in the historical record under `data/history/`. It is not the current two-day picture.

Earlier automated alert from the Aug 16 watch: [ALERT-20260816T152738Z](ALERTS/ALERT-20260816T152738Z.md).

---

## How to read the maps today

- **Glascwm** is the highest-volume / top-ranked cluster — multi-satellite, still **plausible**, not externally confirmed in this publication.
- **Angle** has the newest last-detection among current candidates (**03:42 UTC** on 21 Aug).
- Gower/Swansea shows **no** FIRMS hits in the rolling 24h box — absence of detections is not proof that no fire exists on the ground.
- External corroboration remains a **separate** layer.

---

## Operator tooling

| Script | Purpose |
|---|---|
| `run_all.py` | Full refresh: Wales publication + Gower + VIIRS browse + wales-now + HTML |
| `firms_ping.py` / `watch_and_alert.py` | Poll until latest obs moves; optional alert + GitHub push |
| `pass_calendar.py` / `waiting_room.py` | TLE pass calendar vs FIRMS NRT lag |

---

## Reproduce this refresh

```bash
source .venv/bin/activate
export NASA_FIRMS_MAP_KEY="$(tr -d '\n\r ' < secrets/nasa\ firms.txt)"
python projects/006-wildfire-watch/run_all.py --open
```

---

## Caveats (unchanged)

- Not an official NASA, Welsh Government, NRW or fire-and-rescue product.
- NRT can be revised; later Standard Processing may disagree.
- 375 m VIIRS is product resolution, not GPS pin-point accuracy.
- See [METHODOLOGY.md](METHODOLOGY.md), [SOURCES.md](SOURCES.md), [CORRELATIONS.md](CORRELATIONS.md), [FIGURES.md](FIGURES.md).
