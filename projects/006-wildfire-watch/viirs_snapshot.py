"""NASA GIBS VIIRS browse snapshot for Suomi NPP / NOAA-20 / NOAA-21.

Pulls Worldview-style WMS imagery for a Wales or Swansea–Gower bbox, writes a
manifest, builds per-layer explained figures (like other Project 006 maps), and
a contact-sheet overview. Browse imagery only — not ATMS/CrIS/OMPS granules.
See VIIRS_PRODUCTS.md.
"""
from __future__ import annotations

import argparse
import json
import math
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import matplotlib.pyplot as plt
import requests
from PIL import Image

ROOT = Path(__file__).resolve().parent

GIBS_WMS = "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi"
USER_AGENT = "hinsawdd-cymru-viirs-snapshot/0.1"

WALES_WATCH_BBOX = (-5.6, 51.2, -2.55, 53.5)  # west, south, east, north
SWANSEA_GOWER_BBOX = (-4.35, 51.52, -3.85, 51.72)

SATELLITES = (
    ("SNPP", "VIIRS_SNPP", "Suomi NPP"),
    ("NOAA20", "VIIRS_NOAA20", "NOAA-20"),
    ("NOAA21", "VIIRS_NOAA21", "NOAA-21"),
)

# Default: one bird keeps the review set small (feedback: too many outputs).
DEFAULT_SATELLITE_KEYS = ("NOAA20",)

# theme_key, layer suffix, short label, format, explainer
# Day/Night dropped (noisy daytime). Swansea–Gower crop opt-in only (blurry at this zoom).
THEMES: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "true_color",
        "CorrectedReflectance_TrueColor",
        "True colour",
        "image/jpeg",
        "Natural-looking VIIRS view (bands close to what the eye sees). Use for smoke plumes, cloud, and landscape context. Not a fire confirmation.",
    ),
    (
        "aod",
        "AOD_Deep_Blue_Land_Ocean",
        "AOD Deep Blue",
        "image/png",
        "Aerosol Optical Depth (Deep Blue). Higher values mean thicker haze, smoke, or dust in the air column over that grid cell. Gaps = no retrieval. Wales community outlines are overlaid so you can place the haze relative to land.",
    ),
    (
        "thermal",
        "Thermal_Anomalies_375m_All",
        "Thermal anomalies",
        "image/png",
        "Browse overlay of 375 m thermal anomalies (same family as FIRMS hotspots). Visual only — use the FIRMS CSV for coordinates, time, and FRP. Wales outlines help locate sparse pixels.",
    ),
    (
        "lst_day",
        "Land_Surface_Temp_Day",
        "Land surface temp (day)",
        "image/png",
        "Daytime land surface temperature. Warm land vs cool sea; heat context only, not a wildfire map. Wales outlines show where the land sits under the colour field.",
    ),
    (
        "false_color",
        "SurfaceReflectance_BandsM11-M7-M5",
        "False colour (burn / vegetation)",
        "image/png",
        "False-colour composite using VIIRS bands M11–M7–M5 (shortwave IR / mid-IR / visible-IR). Healthy vegetation often appears green; recently burned or bare ground can show as browns/reds/magenta depending on residue and soil. Clouds stay bright. Use with true colour — not a confirmed burn map.",
    ),
)

THEME_EXPLAINERS = {t[0]: t[4] for t in THEMES}
THEME_LABELS = {t[0]: t[2] for t in THEMES}
SAT_DISPLAY = {s[0]: s[2] for s in SATELLITES}
SAT_BY_KEY = {s[0]: s for s in SATELLITES}

FIG_BG = "#080c16"
AX_BG = "#0f172a"
TEXT = "#f8fafc"
MUTED = "#94a3b8"
GRID = "#334155"
CYAN = "#22d3ee"
BOUNDARY_EDGE = "#e2e8f0"


def _parse_bbox(value: str) -> tuple[float, float, float, float]:
    key = value.strip().lower()
    if key in {"wales", "wales-watch"}:
        return WALES_WATCH_BBOX
    if key in {"swansea-gower", "swansea_gower", "gower"}:
        return SWANSEA_GOWER_BBOX
    parts = [float(x) for x in value.split(",")]
    if len(parts) != 4:
        raise ValueError("bbox must be wales|swansea-gower|west,south,east,north")
    west, south, east, north = parts
    if not (west < east and south < north):
        raise ValueError("bbox requires west<east and south<north")
    return west, south, east, north


def _bbox_label(bbox: tuple[float, float, float, float]) -> str:
    if bbox == WALES_WATCH_BBOX:
        return "wales"
    if bbox == SWANSEA_GOWER_BBOX:
        return "swansea-gower"
    return "custom"


def _wms_bbox_1_3(bbox: tuple[float, float, float, float]) -> str:
    # WMS 1.3.0 + EPSG:4326 uses lat,lon axis order
    west, south, east, north = bbox
    return f"{south},{west},{north},{east}"


def _map_size(bbox: tuple[float, float, float, float], *, max_edge: int = 1400) -> tuple[int, int]:
    west, south, east, north = bbox
    # compensate longitude span by cos(mid-lat) for roughly equal ground metres
    mid_lat = (south + north) / 2.0
    width_deg = (east - west) * max(0.2, math.cos(math.radians(mid_lat)))
    height_deg = north - south
    if width_deg >= height_deg:
        w = max_edge
        h = max(320, int(round(max_edge * height_deg / width_deg)))
    else:
        h = max_edge
        w = max(320, int(round(max_edge * width_deg / height_deg)))
    return w, h


def layer_id(prefix: str, suffix: str) -> str:
    return f"{prefix}_{suffix}"


def fetch_wms_map(
    session: requests.Session,
    *,
    layer: str,
    time_date: str,
    bbox: tuple[float, float, float, float],
    width: int,
    height: int,
    image_format: str,
    timeout: int = 90,
) -> tuple[bytes, str, str]:
    params = {
        "SERVICE": "WMS",
        "REQUEST": "GetMap",
        "VERSION": "1.3.0",
        "LAYERS": layer,
        "STYLES": "",
        "CRS": "EPSG:4326",
        "BBOX": _wms_bbox_1_3(bbox),
        "WIDTH": str(width),
        "HEIGHT": str(height),
        "FORMAT": image_format,
        "TIME": time_date,
        "TRANSPARENT": "TRUE",
    }
    response = session.get(GIBS_WMS, params=params, timeout=timeout)
    content_type = response.headers.get("Content-Type", "")
    # Build a redacted URL for the manifest (no secrets; GIBS is public)
    safe_url = f"{GIBS_WMS}?{urlencode(params)}"
    if response.status_code != 200:
        raise RuntimeError(f"HTTP {response.status_code}: {content_type[:80]}")
    if "image/" not in content_type.lower():
        # GIBS returns XML ServiceException on bad layer/date
        snippet = response.text[:240].replace("\n", " ")
        raise RuntimeError(f"non-image response ({content_type}): {snippet}")
    return response.content, content_type, safe_url


def _ext_for_format(image_format: str) -> str:
    if "jpeg" in image_format or "jpg" in image_format:
        return "jpg"
    return "png"


def figure_stem(area: str, satellite: str, theme: str) -> str:
    return f"viirs_{area}_{satellite}_{theme}_dark"


def _parse_satellites(value: str | None) -> tuple[tuple[str, str, str], ...]:
    if value is None or not str(value).strip():
        keys = list(DEFAULT_SATELLITE_KEYS)
    else:
        raw = str(value).strip().lower()
        if raw in {"all", "*"}:
            keys = [s[0] for s in SATELLITES]
        else:
            keys = []
            for part in raw.replace(";", ",").split(","):
                token = part.strip().upper().replace("-", "").replace("_", "")
                if token in {"SNPP", "SUOMINPP", "NPP"}:
                    keys.append("SNPP")
                elif token in {"NOAA20", "N20", "JPSS1"}:
                    keys.append("NOAA20")
                elif token in {"NOAA21", "N21", "JPSS2"}:
                    keys.append("NOAA21")
                else:
                    raise ValueError(f"Unknown satellite token: {part!r} (use NOAA20|SNPP|NOAA21|all)")
    out = []
    seen = set()
    for key in keys:
        if key in seen:
            continue
        seen.add(key)
        out.append(SAT_BY_KEY[key])
    if not out:
        raise ValueError("No satellites selected")
    return tuple(out)


def _load_wales_boundary() -> dict | None:
    candidates = [
        ROOT / "published" / "data" / "reference" / "communities_wales.geojson",
        ROOT / "published" / "local" / "swansea-gower" / "data" / "reference" / "communities_wales.geojson",
    ]
    for path in candidates:
        if path.exists():
            return json.loads(path.read_text())
    return None


def _draw_wales_outline(ax, boundary: dict, bbox: tuple[float, float, float, float]) -> None:
    west, south, east, north = bbox
    pad = 0.15
    for feature in boundary.get("features", []):
        geom = feature.get("geometry") or {}
        gtype = geom.get("type")
        coords = geom.get("coordinates")
        if not coords:
            continue
        polys = [coords] if gtype == "Polygon" else (coords if gtype == "MultiPolygon" else [])
        for poly in polys:
            if not poly:
                continue
            ring = poly[0]
            xs = [float(p[0]) for p in ring]
            ys = [float(p[1]) for p in ring]
            if max(xs) < west - pad or min(xs) > east + pad or max(ys) < south - pad or min(ys) > north + pad:
                continue
            ax.plot(xs, ys, color=BOUNDARY_EDGE, linewidth=0.55, alpha=0.9, zorder=5)


def build_explained_figure(
    *,
    image_path: Path,
    out_path: Path,
    satellite: str,
    theme_key: str,
    time_date: str,
    area: str,
    layer: str,
    bbox: list[float] | tuple[float, float, float, float],
    boundary: dict | None = None,
) -> Path:
    theme_label = THEME_LABELS.get(theme_key, theme_key)
    explainer = THEME_EXPLAINERS.get(theme_key, "")
    sat_name = SAT_DISPLAY.get(satellite, satellite)
    west, south, east, north = bbox

    img = Image.open(image_path)
    aspect = img.width / max(1, img.height)
    fig_w = 12.5
    fig_h = max(8.2, fig_w / aspect + 2.2)
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=160, facecolor=FIG_BG)
    ax = fig.add_axes([0.06, 0.22, 0.90, 0.70])
    ax.set_facecolor(AX_BG)
    ax.imshow(img, extent=(west, east, south, north), origin="upper", aspect="equal")
    if boundary is not None:
        _draw_wales_outline(ax, boundary, (west, south, east, north))
    ax.set_xlim(west, east)
    ax.set_ylim(south, north)
    ax.set_xlabel("Longitude", color=MUTED, fontsize=11)
    ax.set_ylabel("Latitude", color=MUTED, fontsize=11)
    ax.tick_params(colors=MUTED, labelsize=10)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.grid(True, color=GRID, alpha=0.22, linewidth=0.5)
    ax.set_axisbelow(True)

    ax.set_title(
        f"{sat_name} VIIRS — {theme_label}\n{area} · GIBS browse · {time_date}",
        color=TEXT,
        fontsize=15,
        pad=12,
    )

    caption = fig.add_axes([0.06, 0.03, 0.90, 0.16])
    caption.set_facecolor(FIG_BG)
    caption.axis("off")
    wrapped = textwrap.fill(explainer, width=100)
    caption.text(
        0.0,
        0.95,
        wrapped,
        ha="left",
        va="top",
        color=TEXT,
        fontsize=11,
        wrap=True,
        transform=caption.transAxes,
    )
    caption.text(
        0.0,
        0.08,
        f"Layer: {layer}  ·  Browse imagery only — not confirmed wildfire evidence. FIRMS CSV remains the hotspot table.",
        ha="left",
        va="bottom",
        color=MUTED,
        fontsize=9,
        transform=caption.transAxes,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    return out_path


def write_explainers_md(
    *,
    run_dir: Path,
    time_date: str,
    generated_at: str,
    records: list[dict[str, Any]],
    gower_records: list[dict[str, Any]],
) -> Path:
    lines = [
        f"# VIIRS GIBS browse figures — {time_date}",
        "",
        f"Generated `{generated_at}`. Each PNG is a single satellite × product frame with an on-image explainer.",
        "Contact sheets remain overview grids only.",
        "",
        "## Wales watch bbox",
        "",
        "| Figure | Satellite | Product | Status |",
        "|---|---|---|---|",
    ]
    for r in records:
        stem = figure_stem(r["area"], r["satellite"], r["theme"])
        rel = f"{stem}.png"
        status = "ok" if r.get("figure") else r.get("status", "error")
        lines.append(
            f"| [`{stem}.png`]({rel}) | {SAT_DISPLAY.get(r['satellite'], r['satellite'])} | {r['theme_label']} | {status} |"
        )
        if r.get("status") == "ok":
            lines.append("")
            lines.append(f"**{r['theme_label']} ({r['satellite']})** — {THEME_EXPLAINERS.get(r['theme'], '')}")
            lines.append("")

    if gower_records:
        lines.extend(
            [
                "## Swansea–Gower crop",
                "",
                "| Figure | Satellite | Product | Status |",
                "|---|---|---|---|",
            ]
        )
        for r in gower_records:
            stem = figure_stem(r["area"], r["satellite"], r["theme"])
            rel = f"{stem}.png"
            status = "ok" if r.get("figure") else r.get("status", "error")
            lines.append(
                f"| [`{stem}.png`]({rel}) | {SAT_DISPLAY.get(r['satellite'], r['satellite'])} | {r['theme_label']} | {status} |"
            )

    path = run_dir / "figures" / "EXPLAINERS.md"
    path.write_text("\n".join(lines).rstrip() + "\n")
    return path


def _feedback_items(records: list[dict[str, Any]], gower_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for r in list(records) + list(gower_records):
        stem = figure_stem(r["area"], r["satellite"], r["theme"])
        items.append(
            {
                "figure_id": stem,
                "figure_file": r.get("figure") or f"figures/{stem}.png",
                "satellite": r["satellite"],
                "satellite_display": SAT_DISPLAY.get(r["satellite"], r["satellite"]),
                "theme": r["theme"],
                "theme_label": r["theme_label"],
                "area": r["area"],
                "layer": r.get("layer"),
                "status": r.get("status"),
                "explainer": THEME_EXPLAINERS.get(r["theme"], ""),
                "has_image": bool(r.get("figure") and r.get("status") == "ok"),
            }
        )
    return items


def write_feedback_html(
    *,
    run_dir: Path,
    stamp: str,
    time_date: str,
    generated_at: str,
    records: list[dict[str, Any]],
    gower_records: list[dict[str, Any]],
) -> Path:
    """Write review.html with inline images and per-figure feedback boxes → feedback.json."""
    import html as html_lib

    items = _feedback_items(records, gower_records)
    items_json = json.dumps(items, indent=2)

    cards: list[str] = []
    for item in items:
        fid = item["figure_id"]
        fid_attr = html_lib.escape(fid, quote=True)
        title = html_lib.escape(f"{item['satellite_display']} — {item['theme_label']} ({item['area']})")
        explainer = html_lib.escape(item["explainer"])
        layer = html_lib.escape(str(item.get("layer") or ""))
        status = html_lib.escape(str(item.get("status") or ""))
        if item["has_image"]:
            # review.html lives in run_dir; figures are relative
            src = html_lib.escape(item["figure_file"], quote=True)
            media = f'<img src="{src}" alt="{fid_attr}" loading="lazy">'
        else:
            media = f'<div class="missing">No image ({status}). You can still leave feedback on this slot.</div>'
        cards.append(
            f"""
    <section class="card" id="{fid_attr}" data-figure-id="{fid_attr}">
      <header>
        <h2>{title}</h2>
        <p class="meta"><code>{fid_attr}</code> · status: {status} · layer: <code>{layer}</code></p>
        <p class="explainer">{explainer}</p>
      </header>
      <div class="media">{media}</div>
      <label class="feedback-label" for="fb-{fid_attr}">Your feedback for <strong>{fid_attr}</strong></label>
      <textarea id="fb-{fid_attr}" class="feedback" data-figure-id="{fid_attr}"
        placeholder="Notes for this figure only (layout, crop, labels, usefulness, bugs)…"
        rows="4"></textarea>
    </section>"""
        )

    cards_html = "\n".join(cards)
    stamp_esc = html_lib.escape(stamp)
    time_esc = html_lib.escape(time_date)
    gen_esc = html_lib.escape(generated_at)

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIIRS browse feedback — {time_esc}</title>
<style>
  :root {{
    --bg: #080c16;
    --card: #0f172a;
    --text: #f8fafc;
    --muted: #94a3b8;
    --line: #334155;
    --accent: #22d3ee;
    --btn: #1d4ed8;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font: 15px/1.45 system-ui, -apple-system, Segoe UI, sans-serif;
    background: var(--bg);
    color: var(--text);
  }}
  .topbar {{
    position: sticky; top: 0; z-index: 20;
    display: flex; flex-wrap: wrap; gap: 10px; align-items: center;
    justify-content: space-between;
    padding: 12px 18px;
    background: rgba(8,12,22,0.94);
    border-bottom: 1px solid var(--line);
    backdrop-filter: blur(8px);
  }}
  .topbar h1 {{ margin: 0; font-size: 1.05rem; font-weight: 650; }}
  .topbar p {{ margin: 2px 0 0; color: var(--muted); font-size: 0.85rem; }}
  .actions {{ display: flex; flex-wrap: wrap; gap: 8px; }}
  button {{
    appearance: none; border: 0; border-radius: 8px;
    padding: 10px 14px; font-weight: 600; cursor: pointer;
    background: var(--btn); color: white;
  }}
  button.secondary {{ background: #334155; }}
  button:hover {{ filter: brightness(1.08); }}
  #status {{ color: var(--accent); font-size: 0.85rem; min-height: 1.2em; }}
  main {{ max-width: 980px; margin: 0 auto; padding: 18px 16px 80px; }}
  .card {{
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 16px;
    margin: 0 0 22px;
  }}
  .card h2 {{ margin: 0 0 6px; font-size: 1.15rem; }}
  .meta {{ color: var(--muted); font-size: 0.82rem; margin: 0 0 8px; }}
  .explainer {{ margin: 0 0 12px; color: #cbd5e1; }}
  .media {{
    background: #020617;
    border: 1px solid var(--line);
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 12px;
  }}
  .media img {{ display: block; width: 100%; height: auto; }}
  .missing {{
    padding: 40px 16px; text-align: center; color: var(--muted);
  }}
  .feedback-label {{ display: block; margin: 0 0 6px; color: var(--muted); font-size: 0.9rem; }}
  textarea.feedback {{
    width: 100%;
    resize: vertical;
    min-height: 88px;
    padding: 10px 12px;
    border-radius: 8px;
    border: 1px solid var(--line);
    background: #020617;
    color: var(--text);
    font: inherit;
  }}
  textarea.feedback:focus {{ outline: 2px solid var(--accent); border-color: transparent; }}
  code {{ color: #a5f3fc; }}
  .toc {{ margin: 0 0 24px; padding: 12px 14px; border: 1px dashed var(--line); border-radius: 10px; }}
  .toc a {{ color: var(--accent); margin-right: 10px; font-size: 0.85rem; }}
</style>
</head>
<body>
  <div class="topbar">
    <div>
      <h1>VIIRS GIBS browse feedback</h1>
      <p>Snapshot <code>{stamp_esc}</code> · date {time_esc} · generated {gen_esc}</p>
      <div id="status"></div>
    </div>
    <div class="actions">
      <button type="button" class="secondary" id="btn-load">Load feedback.json</button>
      <button type="button" id="btn-save">Save feedback.json</button>
    </div>
  </div>
  <main>
    <p class="explainer">
      Each text box is tied to one <code>figure_id</code> (same stem as the PNG).
      Click <strong>Save feedback.json</strong> when finished — put the file in this snapshot folder
      (<code>{stamp_esc}/feedback.json</code>) so Cursor can read your notes and apply changes.
      Drafts also autosave in this browser.
    </p>
    <nav class="toc" id="toc"></nav>
{cards_html}
  </main>
<script>
const SNAPSHOT_STAMP = {json.dumps(stamp)};
const TIME_DATE = {json.dumps(time_date)};
const GENERATED_AT = {json.dumps(generated_at)};
const ITEMS = {items_json};
const STORAGE_KEY = "viirs-browse-feedback:" + SNAPSHOT_STAMP;

function setStatus(msg) {{
  document.getElementById("status").textContent = msg || "";
}}

function collectPayload() {{
  const byId = Object.fromEntries(ITEMS.map(i => [i.figure_id, i]));
  const items = [];
  document.querySelectorAll("textarea.feedback").forEach((el) => {{
    const id = el.getAttribute("data-figure-id");
    const base = byId[id] || {{ figure_id: id }};
    items.push({{
      figure_id: id,
      figure_file: base.figure_file || null,
      satellite: base.satellite || null,
      satellite_display: base.satellite_display || null,
      theme: base.theme || null,
      theme_label: base.theme_label || null,
      area: base.area || null,
      layer: base.layer || null,
      status: base.status || null,
      feedback: el.value.trim()
    }});
  }});
  return {{
    schema: "hinsawdd-cymru/viirs-browse-feedback/v1",
    snapshot_stamp: SNAPSHOT_STAMP,
    time_date: TIME_DATE,
    snapshot_generated_at_utc: GENERATED_AT,
    saved_at_utc: new Date().toISOString(),
    item_count: items.length,
    filled_count: items.filter(i => i.feedback).length,
    items
  }};
}}

function applyFeedbackMap(map) {{
  document.querySelectorAll("textarea.feedback").forEach((el) => {{
    const id = el.getAttribute("data-figure-id");
    if (Object.prototype.hasOwnProperty.call(map, id)) el.value = map[id] || "";
  }});
}}

function persistLocal() {{
  const payload = collectPayload();
  const map = Object.fromEntries(payload.items.map(i => [i.figure_id, i.feedback]));
  localStorage.setItem(STORAGE_KEY, JSON.stringify({{ saved_at_utc: payload.saved_at_utc, map }}));
}}

function restoreLocal() {{
  try {{
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    const data = JSON.parse(raw);
    if (data && data.map) applyFeedbackMap(data.map);
    setStatus("Restored draft from this browser");
  }} catch (e) {{
    setStatus("Could not restore draft");
  }}
}}

async function saveFeedback() {{
  const payload = collectPayload();
  const text = JSON.stringify(payload, null, 2);
  persistLocal();

  // Prefer writing feedback.json via File System Access API when available
  if (window.showSaveFilePicker) {{
    try {{
      const handle = await window.showSaveFilePicker({{
        suggestedName: "feedback.json",
        types: [{{ description: "JSON", accept: {{ "application/json": [".json"] }} }}]
      }});
      const writable = await handle.createWritable();
      await writable.write(text);
      await writable.close();
      setStatus("Saved feedback.json (" + payload.filled_count + " notes filled). Leave it in folder " + SNAPSHOT_STAMP + "/");
      return;
    }} catch (e) {{
      if (e && e.name === "AbortError") {{
        setStatus("Save cancelled");
        return;
      }}
      // fall through to download
    }}
  }}

  const blob = new Blob([text], {{ type: "application/json" }});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "feedback.json";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
  setStatus("Downloaded feedback.json (" + payload.filled_count + " notes). Move it into " + SNAPSHOT_STAMP + "/");
}}

async function loadFeedback() {{
  if (window.showOpenFilePicker) {{
    try {{
      const [handle] = await window.showOpenFilePicker({{
        types: [{{ description: "JSON", accept: {{ "application/json": [".json"] }} }}]
      }});
      const file = await handle.getFile();
      const data = JSON.parse(await file.text());
      const map = {{}};
      (data.items || []).forEach((i) => {{ map[i.figure_id] = i.feedback || ""; }});
      applyFeedbackMap(map);
      persistLocal();
      setStatus("Loaded feedback.json");
      return;
    }} catch (e) {{
      if (e && e.name === "AbortError") return;
    }}
  }}
  const input = document.createElement("input");
  input.type = "file";
  input.accept = "application/json,.json";
  input.onchange = async () => {{
    const file = input.files && input.files[0];
    if (!file) return;
    const data = JSON.parse(await file.text());
    const map = {{}};
    (data.items || []).forEach((i) => {{ map[i.figure_id] = i.feedback || ""; }});
    applyFeedbackMap(map);
    persistLocal();
    setStatus("Loaded " + file.name);
  }};
  input.click();
}}

function buildToc() {{
  const nav = document.getElementById("toc");
  nav.innerHTML = "<strong>Jump:</strong> ";
  ITEMS.forEach((item) => {{
    const a = document.createElement("a");
    a.href = "#" + item.figure_id;
    a.textContent = item.figure_id.replace(/^viirs_/, "");
    nav.appendChild(a);
  }});
}}

document.getElementById("btn-save").addEventListener("click", () => {{ saveFeedback(); }});
document.getElementById("btn-load").addEventListener("click", () => {{ loadFeedback(); }});
document.querySelectorAll("textarea.feedback").forEach((el) => {{
  el.addEventListener("input", () => {{ persistLocal(); }});
}});
buildToc();
restoreLocal();
</script>
</body>
</html>
"""
    path = run_dir / "review.html"
    path.write_text(page)
    return path


def write_review_bundle_from_manifest(run_dir: Path) -> dict[str, Any]:
    """Regenerate review.html / EXPLAINERS from an existing stamp folder."""
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    stamp = run_dir.name
    records = manifest.get("layers") or []
    gower_records = manifest.get("swansea_gower_layers") or []
    explainers = write_explainers_md(
        run_dir=run_dir,
        time_date=str(manifest.get("time_date")),
        generated_at=str(manifest.get("generated_at_utc")),
        records=records,
        gower_records=gower_records,
    )
    review = write_feedback_html(
        run_dir=run_dir,
        stamp=stamp,
        time_date=str(manifest.get("time_date")),
        generated_at=str(manifest.get("generated_at_utc")),
        records=records,
        gower_records=gower_records,
    )
    manifest["explainers_md"] = str(explainers.relative_to(run_dir))
    manifest["review_html"] = str(review.relative_to(run_dir))
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return {"run_dir": str(run_dir), "review_html": str(review), "explainers_md": str(explainers)}


def _pull_theme_set(
    session: requests.Session,
    *,
    themes: tuple[tuple[str, str, str, str, str], ...] | list[tuple[str, str, str, str, str]],
    satellites: tuple[tuple[str, str, str], ...],
    bbox: tuple[float, float, float, float],
    area: str,
    time_date: str,
    width: int,
    height: int,
    raw_dir: Path,
    run_dir: Path,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for sat_key, prefix, _sat_name in satellites:
        for theme_key, suffix, theme_label, image_format, _explainer in themes:
            lid = layer_id(prefix, suffix)
            filename = f"{sat_key}_{theme_key}.{_ext_for_format(image_format)}"
            out_path = raw_dir / filename
            entry: dict[str, Any] = {
                "satellite": sat_key,
                "theme": theme_key,
                "theme_label": theme_label,
                "layer": lid,
                "time": time_date,
                "bbox": list(bbox),
                "area": area,
                "width": width,
                "height": height,
                "format": image_format,
                "path": str(out_path.relative_to(run_dir)),
                "status": "pending",
                "figure": None,
            }
            try:
                payload, content_type, safe_url = fetch_wms_map(
                    session,
                    layer=lid,
                    time_date=time_date,
                    bbox=bbox,
                    width=width,
                    height=height,
                    image_format=image_format,
                )
                out_path.write_bytes(payload)
                entry.update(
                    {
                        "status": "ok",
                        "bytes": len(payload),
                        "content_type": content_type,
                        "url": safe_url,
                    }
                )
            except Exception as exc:  # noqa: BLE001 — record per-layer failures
                entry.update(
                    {
                        "status": "error",
                        "error": str(exc),
                        "bytes": 0,
                        "content_type": None,
                        "url": None,
                    }
                )
            records.append(entry)
    return records


def _render_explained_set(
    records: list[dict[str, Any]],
    *,
    run_dir: Path,
    fig_dir: Path,
    boundary: dict | None,
) -> None:
    for entry in records:
        if entry["status"] != "ok":
            continue
        stem = figure_stem(entry["area"], entry["satellite"], entry["theme"])
        fig_path = fig_dir / f"{stem}.png"
        build_explained_figure(
            image_path=run_dir / entry["path"],
            out_path=fig_path,
            satellite=entry["satellite"],
            theme_key=entry["theme"],
            time_date=entry["time"],
            area=entry["area"],
            layer=entry["layer"],
            bbox=entry["bbox"],
            boundary=boundary,
        )
        entry["figure"] = str(fig_path.relative_to(run_dir))


def run_snapshot(
    *,
    time_date: str,
    bbox: tuple[float, float, float, float],
    output_root: Path,
    max_edge: int = 2000,
    also_gower_crop: bool = False,
    satellites: tuple[tuple[str, str, str], ...] | None = None,
) -> dict[str, Any]:
    generated = datetime.now(timezone.utc)
    stamp = generated.strftime("%Y%m%dT%H%M%SZ")
    area = _bbox_label(bbox)
    run_dir = Path(output_root) / stamp
    raw_dir = run_dir / "raw"
    fig_dir = run_dir / "figures"
    raw_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    sat_rows = satellites or _parse_satellites(None)
    boundary = _load_wales_boundary()
    width, height = _map_size(bbox, max_edge=max_edge)

    with requests.Session() as session:
        session.headers.update({"User-Agent": USER_AGENT})
        records = _pull_theme_set(
            session,
            themes=THEMES,
            satellites=sat_rows,
            bbox=bbox,
            area=area,
            time_date=time_date,
            width=width,
            height=height,
            raw_dir=raw_dir,
            run_dir=run_dir,
        )

    _render_explained_set(records, run_dir=run_dir, fig_dir=fig_dir, boundary=boundary)
    contact_path = fig_dir / "viirs_browse_contact_dark.png"
    build_contact_sheet(records, run_dir=run_dir, out_path=contact_path, time_date=time_date, area=area)

    gower_contact: str | None = None
    gower_records: list[dict[str, Any]] = []
    if also_gower_crop and bbox != SWANSEA_GOWER_BBOX:
        gower_raw = run_dir / "raw_swansea_gower"
        gower_raw.mkdir(parents=True, exist_ok=True)
        gw, gh = _map_size(SWANSEA_GOWER_BBOX, max_edge=min(1600, max_edge))
        gower_themes = [t for t in THEMES if t[0] in {"true_color", "aod", "thermal"}]
        with requests.Session() as session:
            session.headers.update({"User-Agent": USER_AGENT})
            gower_records = _pull_theme_set(
                session,
                themes=gower_themes,
                satellites=sat_rows,
                bbox=SWANSEA_GOWER_BBOX,
                area="swansea-gower",
                time_date=time_date,
                width=gw,
                height=gh,
                raw_dir=gower_raw,
                run_dir=run_dir,
            )
        _render_explained_set(gower_records, run_dir=run_dir, fig_dir=fig_dir, boundary=boundary)
        gower_path = fig_dir / "viirs_browse_contact_swansea_gower_dark.png"
        build_contact_sheet(
            gower_records,
            run_dir=run_dir,
            out_path=gower_path,
            time_date=time_date,
            area="swansea-gower",
        )
        gower_contact = str(gower_path.relative_to(run_dir))

    explainers_path = write_explainers_md(
        run_dir=run_dir,
        time_date=time_date,
        generated_at=generated.isoformat(),
        records=records,
        gower_records=gower_records,
    )
    review_path = write_feedback_html(
        run_dir=run_dir,
        stamp=stamp,
        time_date=time_date,
        generated_at=generated.isoformat(),
        records=records,
        gower_records=gower_records,
    )

    figures = [r["figure"] for r in records if r.get("figure")]
    figures += [r["figure"] for r in gower_records if r.get("figure")]

    manifest = {
        "generated_at_utc": generated.isoformat(),
        "time_date": time_date,
        "area": area,
        "bbox": list(bbox),
        "satellites": [s[0] for s in sat_rows],
        "themes": [t[0] for t in THEMES],
        "wales_boundary_overlay": boundary is not None,
        "wms_endpoint": GIBS_WMS,
        "status": "GIBS VIIRS browse imagery; not confirmed wildfire evidence",
        "ok_count": sum(1 for r in records if r["status"] == "ok"),
        "error_count": sum(1 for r in records if r["status"] != "ok"),
        "explained_figures": figures,
        "explainers_md": str(explainers_path.relative_to(run_dir)),
        "review_html": str(review_path.relative_to(run_dir)),
        "feedback_json_hint": "Save review.html → feedback.json into this stamp folder",
        "contact_sheet": str(contact_path.relative_to(run_dir)),
        "swansea_gower_contact_sheet": gower_contact,
        "firms_note": "Hotspot CSV remains the build.py / local_watch.py FIRMS pipeline",
        "layers": records,
        "swansea_gower_layers": gower_records or None,
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    latest = Path(output_root) / "latest"
    latest.mkdir(parents=True, exist_ok=True)
    (latest / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def build_contact_sheet(
    records: list[dict[str, Any]],
    *,
    run_dir: Path,
    out_path: Path,
    time_date: str,
    area: str,
) -> Path:
    sats = []
    seen_s = set()
    for r in records:
        if r["satellite"] not in seen_s:
            sats.append(r["satellite"])
            seen_s.add(r["satellite"])
    if not sats:
        sats = list(DEFAULT_SATELLITE_KEYS)
    themes = []
    seen = set()
    for r in records:
        if r["theme"] not in seen:
            themes.append((r["theme"], r["theme_label"]))
            seen.add(r["theme"])
    if not themes:
        themes = [(t[0], t[2]) for t in THEMES]

    nrows = len(themes)
    ncols = len(sats)
    fig_w = 4.2 * ncols
    fig_h = 3.4 * nrows + 0.8
    fig, axes = plt.subplots(nrows, ncols, figsize=(fig_w, fig_h), dpi=140)
    if nrows == 1 and ncols == 1:
        axes = [[axes]]
    elif nrows == 1:
        axes = [list(axes)]
    elif ncols == 1:
        axes = [[ax] for ax in axes]
    else:
        axes = [list(row) for row in axes]

    fig.patch.set_facecolor(FIG_BG)
    by_key = {(r["satellite"], r["theme"]): r for r in records}

    for i, (theme_key, theme_label) in enumerate(themes):
        for j, sat in enumerate(sats):
            ax = axes[i][j]
            ax.set_facecolor(AX_BG)
            ax.set_xticks([])
            ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_color(GRID)
            rec = by_key.get((sat, theme_key))
            if rec is None:
                ax.text(0.5, 0.5, "n/a", ha="center", va="center", color=MUTED, transform=ax.transAxes)
            elif rec["status"] != "ok":
                msg = str(rec.get("error") or "error")[:80]
                ax.text(
                    0.5,
                    0.5,
                    f"unavailable\n{msg}",
                    ha="center",
                    va="center",
                    color=MUTED,
                    fontsize=7,
                    transform=ax.transAxes,
                    wrap=True,
                )
            else:
                img = Image.open(run_dir / rec["path"])
                ax.imshow(img)
            if i == 0:
                ax.set_title(sat, color=TEXT, fontsize=11, pad=6)
            if j == 0:
                ax.set_ylabel(theme_label, color=MUTED, fontsize=8)

    fig.suptitle(
        f"VIIRS GIBS browse — {area} — {time_date}",
        color=TEXT,
        fontsize=13,
        y=0.995,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.98))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Snapshot NASA GIBS VIIRS browse layers for Wales / Swansea–Gower")
    parser.add_argument("--date", help="UTC date YYYY-MM-DD for GIBS TIME=")
    parser.add_argument(
        "--bbox",
        default="wales",
        help="wales | swansea-gower | west,south,east,north",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "published" / "local" / "viirs-snapshot",
    )
    parser.add_argument("--max-edge", type=int, default=2000, help="Long-edge pixels for WMS GetMap (default 2000)")
    parser.add_argument(
        "--satellites",
        default="NOAA20",
        help="NOAA20 (default) | SNPP | NOAA21 | comma list | all",
    )
    parser.add_argument(
        "--also-gower-crop",
        action="store_true",
        help="Also fetch a Swansea–Gower crop (off by default; often too blurry at this zoom)",
    )
    parser.add_argument(
        "--write-review",
        type=Path,
        help="Regenerate review.html + EXPLAINERS.md for an existing stamp folder (no WMS pull)",
    )
    args = parser.parse_args()
    if args.write_review is not None:
        print(json.dumps(write_review_bundle_from_manifest(Path(args.write_review)), indent=2))
        return
    if not args.date:
        parser.error("--date is required unless --write-review is set")
    bbox = _parse_bbox(args.bbox)
    sat_rows = _parse_satellites(args.satellites)
    manifest = run_snapshot(
        time_date=args.date,
        bbox=bbox,
        output_root=args.output_root,
        max_edge=args.max_edge,
        also_gower_crop=bool(args.also_gower_crop),
        satellites=sat_rows,
    )
    print(
        json.dumps(
            {
                k: manifest[k]
                for k in (
                    "generated_at_utc",
                    "time_date",
                    "area",
                    "satellites",
                    "themes",
                    "ok_count",
                    "error_count",
                    "explainers_md",
                    "review_html",
                    "explained_figures",
                    "contact_sheet",
                    "swansea_gower_contact_sheet",
                )
                if k in manifest
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
