"""Build a local HTML snapshot page for Project 007."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from constants import DERIVED_DIR, FIGURES_DIR, PROJECT_DIR

PUBLISHED_DIR = PROJECT_DIR / "published" / "snapshot"

FIGURE_CARDS = [
    {
        "title": "NW Europe — sea-surface temperature",
        "file": "nw_europe_sst_snapshot_dark.png",
        "what": "Latest-day foundation SST on the Copernicus ODYSSEA ~0.02° grid.",
        "where": "Ireland, Great Britain, Isle of Man and surrounding shelf seas (lon −12°…3°, lat 49°…61°).",
        "how": (
            "Colour = absolute ocean temperature (°C). Dark areas = land or no ocean mask. "
            "The dashed white box marks the Wales shelf window used for the headline time series. "
            "Use this map to see regional context — e.g. how warm the Irish Sea and Celtic Sea are relative to each other."
        ),
    },
    {
        "title": "NW Europe — SST anomaly",
        "file": "nw_europe_sst_anomaly_snapshot_dark.png",
        "what": "Same calendar day, expressed as a departure from the 2019–2023 climatology for that day-of-year.",
        "where": "Same regional window as above.",
        "how": (
            "Red = warmer than the short baseline; blue = cooler. "
            "Shows whether unusual warmth is confined to Wales or part of a wider NE Atlantic shelf pattern. "
            "Not comparable to HadISST 1991–2020 anomalies (different baseline and product)."
        ),
    },
    {
        "title": "Wales shelf — daily history",
        "file": "wales_shelf_sst_daily_history_dark.png",
        "what": "Area-mean daily SST over the Wales shelf box (cosine-latitude weighted ocean cells).",
        "where": "lon −6.5°…−2.6°, lat 51.2°…53.6° — Welsh coastal / shelf seas only.",
        "how": (
            "Top: cyan = observed daily SST; blue = 2019–2023 day-of-year normal. "
            "Bottom: anomaly bars (warm orange / cool blue). "
            "This panel drives the headline numbers at the top of the page."
        ),
    },
    {
        "title": "Wales shelf — anomaly map (detail)",
        "file": "wales_shelf_sst_daily_anomaly_map_dark.png",
        "what": "Full-resolution anomaly field inside the Wales shelf box.",
        "where": "Same as the dashed box on the regional maps.",
        "how": (
            "Shelf-scale spatial detail at native ~0.02° resolution. "
            "Use when you need local patterns (e.g. Bristol Channel vs open Cardigan Bay tendency) "
            "that are averaged out in the headline series."
        ),
    },
    {
        "title": "Pacific ENSO context (not Wales causation)",
        "file": "wales_shelf_sst_daily_enso_context_dark.png",
        "what": "Wales shelf SST anomaly with NOAA Oceanic Niño Index (ONI) below.",
        "where": "Wales anomaly (top); equatorial Pacific ONI (bottom).",
        "how": (
            "ONI describes Pacific ENSO state only. "
            "Project 007 does not claim El Niño directly warms Welsh shelf seas — "
            "this panel is observational context while both signals evolve."
        ),
    },
]


def render_snapshot_html(
    *,
    derived_dir: Path = DERIVED_DIR,
    figures_dir: Path = FIGURES_DIR,
    output_dir: Path = PUBLISHED_DIR,
) -> Path:
    summary = json.loads((derived_dir / "summary_daily.json").read_text())
    latest = summary.get("latest_date", "unknown")
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    refresh_after = summary.get("recommended_refresh_after_utc", "12:30")
    analysis_time = summary.get("analysis_time_utc", "00:00")

    figure_html: list[str] = []
    for card in FIGURE_CARDS:
        fname = card["file"]
        src = Path("../../figures") / fname
        if not (figures_dir / fname).exists():
            continue
        figure_html.append(
            f"<section class='card'>"
            f"<h2>{escape(card['title'])}</h2>"
            f"<dl class='meta'>"
            f"<dt>What</dt><dd>{escape(card['what'])}</dd>"
            f"<dt>Where</dt><dd>{escape(card['where'])}</dd>"
            f"<dt>How to read</dt><dd>{escape(card['how'])}</dd>"
            f"</dl>"
            f"<a href='{escape(str(src))}'><img src='{escape(str(src))}' alt='{escape(card['title'])}'></a>"
            f"</section>"
        )

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Project 007 — NW Europe SST snapshot</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #080c16;
      --panel: #0f172a;
      --text: #f8fafc;
      --muted: #94a3b8;
      --accent: #22d3ee;
      --border: #334155;
    }}
    body {{
      margin: 0;
      font: 16px/1.55 system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
    }}
    header, main {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 20px 24px 40px;
    }}
    header {{
      border-bottom: 1px solid var(--border);
    }}
    h1 {{ margin: 0 0 8px; font-size: 1.65rem; }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      gap: 12px;
      margin: 16px 0;
    }}
    .stat {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 12px 14px;
    }}
    .stat .label {{ color: var(--muted); font-size: 0.85rem; }}
    .stat .value {{ font-size: 1.3rem; color: var(--accent); font-weight: 600; }}
    .note {{ color: var(--muted); font-size: 0.92rem; margin: 10px 0; }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 18px;
      margin: 22px 0;
    }}
    .card h2 {{ margin: 0 0 12px; font-size: 1.15rem; }}
    .meta {{
      margin: 0 0 14px;
      font-size: 0.92rem;
    }}
    .meta dt {{
      color: var(--accent);
      font-weight: 600;
      margin-top: 8px;
    }}
    .meta dd {{
      margin: 4px 0 0;
      color: var(--muted);
    }}
    img {{ width: 100%; height: auto; border-radius: 8px; display: block; }}
    footer {{ color: var(--muted); font-size: 0.85rem; margin-top: 24px; }}
  </style>
</head>
<body>
  <header>
    <h1>Project 007 — NW Europe sea-surface temperature</h1>
    <p class="note">Hinsawdd Cymru · Copernicus ODYSSEA L4 daily analysis · page generated {escape(generated)}</p>
    <div class="stats">
      <div class="stat"><div class="label">Latest analysis day</div><div class="value">{escape(latest)}</div></div>
      <div class="stat"><div class="label">Field centred</div><div class="value">{escape(analysis_time)} UTC</div></div>
      <div class="stat"><div class="label">Wales shelf SST</div><div class="value">{summary.get('latest_sst_c', '—')} °C</div></div>
      <div class="stat"><div class="label">Wales anomaly</div><div class="value">{summary.get('latest_anomaly_c', '—')} °C</div></div>
      <div class="stat"><div class="label">30-day mean anomaly</div><div class="value">{summary.get('mean_anomaly_last_30d_c', '—')} °C</div></div>
    </div>
    <p class="note"><strong>What this is:</strong> satellite-based foundation SST analysis on a ~0.02° grid — not a beach thermometer.
    <strong>Best refresh:</strong> after {escape(refresh_after)} UTC (Copernicus target delivery ~12:00 UTC).
    <strong>Anomaly baseline:</strong> 2019–2023 same calendar day.</p>
  </header>
  <main>
    {''.join(figure_html)}
    <footer>
      Not an official Met Office, Copernicus, NRW or Welsh Government product.
      <a href="https://github.com/GwriPennar/hinsawdd-cymru/tree/main/projects/007-wales-coastal-sst" style="color:var(--accent)">Project 007 on GitHub</a>
      · <a href="../../FIGURES.md" style="color:var(--accent)">Figure registry</a>
      · <a href="../../METHODOLOGY.md" style="color:var(--accent)">Methodology</a>
    </footer>
  </main>
</body>
</html>
"""
    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / "index.html"
    out.write_text(html, encoding="utf-8")
    return out


def main() -> int:
    path = render_snapshot_html()
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
