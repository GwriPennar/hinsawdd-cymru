"""Build a dark local waiting-room page: FIRMS lag × VIIRS pass calendar.

  python projects/006-wildfire-watch/waiting_room.py
  python projects/006-wildfire-watch/waiting_room.py --open
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT = ROOT / "published" / "local" / "pass-calendar"
NRT_HOURS = 3.0


def _load_key() -> str:
    key = os.getenv("NASA_FIRMS_MAP_KEY", "").strip()
    if key:
        return key
    secret = REPO / "secrets" / "nasa firms.txt"
    if secret.exists():
        return secret.read_text().strip().replace("\n", "").replace("\r", "").replace(" ", "")
    raise SystemExit("NASA_FIRMS_MAP_KEY required")


def gather() -> dict:
    import firms_ping as fp
    import pass_calendar as pc

    now = datetime.now(timezone.utc)
    probe = fp.probe(map_key=_load_key(), days=2)
    cal = pc.build_calendar(hours_ahead=30, hours_back=12, sample_s=60, now=now)
    firms = probe.get("uk_latest_obs_utc")
    statuses = [
        pc.status_message(cal, site="wales", firms_latest_obs_utc=firms, now=now),
        pc.status_message(cal, site="gower", firms_latest_obs_utc=firms, now=now),
    ]

    # Expected NRT windows for recent wales passes
    windows = []
    for p in [x for x in cal["passes"] if x["site"] == "wales" and x["minutes_from_now"] <= 0][-4:]:
        t0 = datetime.fromisoformat(p["culmination_utc"])
        due = t0 + timedelta(hours=NRT_HOURS)
        windows.append(
            {
                "sat": p["sat_label"],
                "pass_utc": p["culmination_utc"],
                "nrt_due_utc": due.isoformat(),
                "minutes_until_due": round((due - now).total_seconds() / 60.0, 1),
                "elev_deg": p["elev_deg"],
            }
        )

    return {
        "generated_at_utc": now.isoformat(),
        "vibe": "satellite waiting room",
        "nrt_target_hours": NRT_HOURS,
        "probe": probe,
        "status": statuses,
        "nrt_windows": windows,
        "next_passes": [p for p in cal["passes"] if p["minutes_from_now"] > 0][:10],
        "recent_passes": [p for p in cal["passes"] if p["minutes_from_now"] <= 0][-8:],
        "note": (
            "Global FIRMS VIIRS NRT is typically within ~3 hours of observation (best effort). "
            "UK does not get US/Canada ultra-real-time direct-readout. "
            "Latest-obs only moves when a newer thermal anomaly is published — clean passes stay quiet."
        ),
    }


def render_html(data: dict) -> str:
    wales = next(s for s in data["status"] if s["site"] == "wales")
    gower = next(s for s in data["status"] if s["site"] == "gower")
    probe = data["probe"]
    gen = data["generated_at_utc"][:19].replace("T", " ")

    def rows(passes: list[dict]) -> str:
        if not passes:
            return "<tr><td colspan='5'>none</td></tr>"
        bits = []
        for p in passes:
            when = p["culmination_utc"][:16].replace("T", " ")
            bits.append(
                "<tr>"
                f"<td>{when}</td><td>{p['site']}</td><td>{p['sat_label']}</td>"
                f"<td>{p['elev_deg']}°</td><td>{p['minutes_from_now']:+.0f}m</td>"
                "</tr>"
            )
        return "".join(bits)

    win_rows = []
    for w in data.get("nrt_windows", []):
        due = w["nrt_due_utc"][:16].replace("T", " ")
        left = w["minutes_until_due"]
        state = "due soon" if left > 0 else "past NRT target"
        win_rows.append(
            f"<tr><td>{w['sat']}</td><td>{w['pass_utc'][11:16]}</td>"
            f"<td>{due}</td><td>{left:+.0f}m</td><td>{state}</td></tr>"
        )
    if not win_rows:
        win_rows.append("<tr><td colspan='5'>no recent wales passes</td></tr>")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Hinsawdd waiting room — FIRMS × VIIRS</title>
<style>
  :root {{
    --bg: #080c16; --panel: #0f172a; --text: #f8fafc; --muted: #94a3b8;
    --grid: #334155; --cyan: #22d3ee; --amber: #f59e0b; --pink: #fb7185;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; min-height: 100vh; background:
      radial-gradient(1200px 600px at 10% -10%, #12203a 0%, transparent 55%),
      radial-gradient(900px 500px at 90% 0%, #1a1030 0%, transparent 50%),
      var(--bg);
    color: var(--text); font: 15px/1.45 "IBM Plex Sans", "Segoe UI", sans-serif;
  }}
  main {{ max-width: 920px; margin: 0 auto; padding: 2.4rem 1.4rem 3rem; }}
  .brand {{ font-size: 0.78rem; letter-spacing: 0.18em; text-transform: uppercase; color: var(--cyan); }}
  h1 {{ font-family: "Iowan Old Style", "Palatino Linotype", Palatino, serif;
       font-weight: 600; font-size: clamp(1.8rem, 4vw, 2.6rem); margin: 0.35rem 0 0.5rem; line-height: 1.15; }}
  .sub {{ color: var(--muted); max-width: 40rem; }}
  .pulse {{
    display: inline-block; width: 0.55rem; height: 0.55rem; border-radius: 50%;
    background: var(--amber); box-shadow: 0 0 0 0 rgba(245,158,11,0.55);
    animation: ping 2.2s ease-out infinite; margin-right: 0.45rem; vertical-align: middle;
  }}
  @keyframes ping {{
    0% {{ box-shadow: 0 0 0 0 rgba(245,158,11,0.5); }}
    70% {{ box-shadow: 0 0 0 12px rgba(245,158,11,0); }}
    100% {{ box-shadow: 0 0 0 0 rgba(245,158,11,0); }}
  }}
  .grid {{ display: grid; gap: 1rem; margin-top: 1.6rem; }}
  @media (min-width: 720px) {{ .grid.two {{ grid-template-columns: 1fr 1fr; }} }}
  section {{
    background: color-mix(in srgb, var(--panel) 88%, transparent);
    border: 1px solid var(--grid); border-radius: 14px; padding: 1rem 1.1rem 1.15rem;
  }}
  h2 {{ margin: 0 0 0.65rem; font-size: 0.95rem; color: var(--muted); font-weight: 600;
       letter-spacing: 0.04em; text-transform: uppercase; }}
  .line {{ font-size: 1.02rem; }}
  .wales {{ color: var(--cyan); }}
  .gower {{ color: var(--amber); }}
  .stat {{ font-variant-numeric: tabular-nums; }}
  .big {{ font-size: 1.35rem; font-weight: 600; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.86rem; }}
  th, td {{ text-align: left; padding: 0.35rem 0.3rem; border-bottom: 1px solid var(--grid); }}
  th {{ color: var(--muted); font-weight: 500; }}
  footer {{ margin-top: 1.4rem; color: var(--muted); font-size: 0.78rem; max-width: 42rem; }}
  .meta {{ margin-top: 0.8rem; color: var(--muted); font-size: 0.8rem; }}
</style>
</head>
<body>
<main>
  <div class="brand">Hinsawdd Cymru · Project 006</div>
  <h1><span class="pulse"></span>Waiting room</h1>
  <p class="sub">Satellites already flew. FIRMS is still thinking. Music optional. Refresh this page after re-running <code>waiting_room.py</code>.</p>

  <div class="grid two">
    <section>
      <h2>Wales</h2>
      <p class="line wales">{wales["line"]}</p>
    </section>
    <section>
      <h2>Gower</h2>
      <p class="line gower">{gower["line"]}</p>
    </section>
  </div>

  <div class="grid two" style="margin-top:1rem">
    <section>
      <h2>Latest FIRMS obs (UK API)</h2>
      <p class="big stat">{(probe.get("uk_latest_obs_utc") or "—")[:19]}</p>
      <p class="meta">UK detections: <span class="stat">{probe.get("uk_detection_count")}</span> ·
      Gower: <span class="stat">{probe.get("gower_detection_count")}</span> ·
      Gower latest: <span class="stat">{(probe.get("gower_latest_obs_utc") or "—")[:19]}</span></p>
    </section>
    <section>
      <h2>~3h NRT windows (recent Wales passes)</h2>
      <table>
        <thead><tr><th>sat</th><th>pass</th><th>NRT due</th><th>left</th><th></th></tr></thead>
        <tbody>{''.join(win_rows)}</tbody>
      </table>
    </section>
  </div>

  <div class="grid two" style="margin-top:1rem">
    <section>
      <h2>Recent culminations</h2>
      <table>
        <thead><tr><th>UTC</th><th>site</th><th>sat</th><th>elev</th><th>Δ</th></tr></thead>
        <tbody>{rows(data.get("recent_passes", []))}</tbody>
      </table>
    </section>
    <section>
      <h2>Next culminations</h2>
      <table>
        <thead><tr><th>UTC</th><th>site</th><th>sat</th><th>elev</th><th>Δ</th></tr></thead>
        <tbody>{rows(data.get("next_passes", []))}</tbody>
      </table>
    </section>
  </div>

  <p class="meta">Generated {gen} UTC · mode <code>{wales["mode"]}</code></p>
  <footer>{data["note"]}</footer>
</main>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="FIRMS × pass-calendar waiting room")
    parser.add_argument("--open", action="store_true")
    parser.add_argument("--output-root", type=Path, default=OUT)
    args = parser.parse_args()

    data = gather()
    out = Path(args.output_root)
    out.mkdir(parents=True, exist_ok=True)
    (out / "waiting_room.json").write_text(json.dumps(data, indent=2) + "\n")
    html_path = out / "waiting_room.html"
    html_path.write_text(render_html(data))

    # Keep calendar figure warm if present
    try:
        import pass_calendar as pc

        cal = pc.build_calendar(hours_ahead=30, hours_back=12, sample_s=60)
        cal["status"] = data["status"]
        (out / "pass_calendar.json").write_text(json.dumps(cal, indent=2) + "\n")
        pc.render_figure(cal, data["status"], out / "figures" / "viirs_pass_calendar_dark")
    except Exception as exc:  # noqa: BLE001
        print(f"figure skipped: {exc}", flush=True)

    print(json.dumps({"event": "WAITING_ROOM", "html": str(html_path), "mode": data["status"][0]["mode"]}, indent=2))
    print(data["status"][0]["line"])
    if args.open:
        subprocess.run(["open", str(html_path)], check=False)
        fig = out / "figures" / "viirs_pass_calendar_dark.png"
        if fig.exists():
            subprocess.run(["open", str(fig)], check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
