"""VIIRS overpass calendar for Wales / Gower — why FIRMS is quiet vs lagging.

  python projects/006-wildfire-watch/pass_calendar.py
  python projects/006-wildfire-watch/pass_calendar.py --hours-ahead 36 --hours-back 18 --figure

TLE-based culmination estimates (not FIRMS processing timestamps). Useful for
telling "no pass until 13:40 UTC" from "pass was 20 min ago — waiting on FIRMS".
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Mid-Wales and Swansea/Gower centres (same family as run_all / local_watch).
SITES: dict[str, tuple[float, float]] = {
    "wales": (52.30, -3.80),
    "gower": (51.62, -4.10),
}

SATELLITES: dict[str, str] = {
    "SNPP": "SUOMI NPP",
    "NOAA20": "NOAA 20",
    "NOAA21": "NOAA 21",
}

DEFAULT_MIN_ELEV_DEG = 8.0
DEFAULT_SAMPLE_S = 30
FIRMS_LAG_HINT_HOURS = 3.0


@dataclass(frozen=True)
class PassEvent:
    site: str
    sat_label: str
    culmination_utc: str  # ISO8601
    elev_deg: float
    nadir_km: float
    minutes_from_now: float


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _match_station(stations: list, label_key: str):
    """Map our short label to a CelesTrak weather TLE entry."""
    want = SATELLITES[label_key].upper()
    for sat in stations:
        name = sat.name.upper()
        if label_key == "SNPP" and "NPP" in name:
            return sat
        if label_key == "NOAA20" and "NOAA 20" in name:
            return sat
        if label_key == "NOAA21" and "NOAA 21" in name:
            return sat
        if want in name:
            return sat
    return None


def find_culmination_passes(
    *,
    stations: list,
    ts,
    wgs84,
    site: str,
    lat: float,
    lon: float,
    sat_label: str,
    sat,
    start: datetime,
    end: datetime,
    min_elev_deg: float = DEFAULT_MIN_ELEV_DEG,
    sample_s: int = DEFAULT_SAMPLE_S,
    now: datetime | None = None,
) -> list[PassEvent]:
    """Sample elevation and keep local maxima above ``min_elev_deg``."""
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    start = start.astimezone(timezone.utc)
    end = end.astimezone(timezone.utc)
    if end <= start:
        return []

    observer = wgs84.latlon(lat, lon)
    samples: list[tuple[datetime, float, float]] = []
    t = start
    step = timedelta(seconds=sample_s)
    while t <= end:
        ti = ts.from_datetime(t)
        elev = (sat - observer).at(ti).altaz()[0].degrees
        sub = wgs84.subpoint_of(sat.at(ti))
        nadir = haversine_km(lat, lon, sub.latitude.degrees, sub.longitude.degrees)
        samples.append((t, elev, nadir))
        t += step

    events: list[PassEvent] = []
    for i in range(1, len(samples) - 1):
        t_i, elev_i, nadir_i = samples[i]
        if elev_i < min_elev_deg:
            continue
        if elev_i >= samples[i - 1][1] and elev_i >= samples[i + 1][1]:
            events.append(
                PassEvent(
                    site=site,
                    sat_label=sat_label,
                    culmination_utc=t_i.isoformat(),
                    elev_deg=round(elev_i, 1),
                    nadir_km=round(nadir_i, 0),
                    minutes_from_now=round((t_i - now).total_seconds() / 60.0, 1),
                )
            )
    return events


def load_weather_stations(*, cache_dir: Path | None = None):
    from skyfield.api import Loader

    cache_dir = cache_dir or (REPO / ".skyfield-cache")
    loader = Loader(str(cache_dir))
    ts = loader.timescale()
    stations = loader.tle_file("https://celestrak.org/NORAD/elements/gp.php?GROUP=weather&FORMAT=tle")
    return loader, ts, stations


def build_calendar(
    *,
    now: datetime | None = None,
    hours_ahead: float = 36.0,
    hours_back: float = 18.0,
    min_elev_deg: float = DEFAULT_MIN_ELEV_DEG,
    sample_s: int = DEFAULT_SAMPLE_S,
    sites: dict[str, tuple[float, float]] | None = None,
    cache_dir: Path | None = None,
) -> dict:
    from skyfield.api import wgs84

    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    sites = sites or SITES
    _, ts, stations = load_weather_stations(cache_dir=cache_dir)
    start = now - timedelta(hours=hours_back)
    end = now + timedelta(hours=hours_ahead)

    passes: list[PassEvent] = []
    missing: list[str] = []
    for sat_label in SATELLITES:
        sat = _match_station(stations, sat_label)
        if sat is None:
            missing.append(sat_label)
            continue
        for site, (lat, lon) in sites.items():
            passes.extend(
                find_culmination_passes(
                    stations=stations,
                    ts=ts,
                    wgs84=wgs84,
                    site=site,
                    lat=lat,
                    lon=lon,
                    sat_label=sat_label,
                    sat=sat,
                    start=start,
                    end=end,
                    min_elev_deg=min_elev_deg,
                    sample_s=sample_s,
                    now=now,
                )
            )

    passes_sorted = sorted(passes, key=lambda p: p.culmination_utc)
    return {
        "generated_at_utc": now.isoformat(),
        "hours_back": hours_back,
        "hours_ahead": hours_ahead,
        "min_elev_deg": min_elev_deg,
        "sample_s": sample_s,
        "sites": {k: {"lat": v[0], "lon": v[1]} for k, v in sites.items()},
        "satellites": SATELLITES,
        "missing_satellites": missing,
        "pass_count": len(passes_sorted),
        "passes": [asdict(p) for p in passes_sorted],
        "note": (
            "Culmination times are TLE geometry estimates near each site centre. "
            "They are not FIRMS acquisition or processing timestamps; NRT lag after "
            "a useful pass is often tens of minutes to a few hours."
        ),
    }


def status_message(
    calendar: dict,
    *,
    site: str = "wales",
    firms_latest_obs_utc: str | None = None,
    now: datetime | None = None,
) -> dict:
    """One-line operator status: quiet vs FIRMS lag vs pass opening soon."""
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    site_passes = [p for p in calendar.get("passes", []) if p["site"] == site]
    past = [p for p in site_passes if p["minutes_from_now"] <= 0]
    future = [p for p in site_passes if p["minutes_from_now"] > 0]
    last_pass = past[-1] if past else None
    next_pass = future[0] if future else None

    mode = "unknown"
    line = "No useful VIIRS culminations in the calendar window."
    # Prefer lag diagnosis when a useful pass already happened recently —
    # that is the usual reason a FIRMS ping sits on refreshed:false overnight.
    if last_pass and (-last_pass["minutes_from_now"]) <= FIRMS_LAG_HINT_HOURS * 60:
        ago = -last_pass["minutes_from_now"]
        mode = "firms_lag_window"
        line = (
            f"Pass was ~{ago:.0f} min ago ({last_pass['sat_label']} {site} "
            f"{last_pass['culmination_utc'][11:16]} UTC, elev {last_pass['elev_deg']}°) — "
            f"waiting on FIRMS NRT lag, not geometry."
        )
        if firms_latest_obs_utc:
            line += f" Latest FIRMS obs still {firms_latest_obs_utc[:16]}."
        if next_pass and next_pass["minutes_from_now"] <= 90:
            line += (
                f" Next pass ~{next_pass['culmination_utc'][11:16]} UTC "
                f"({next_pass['sat_label']}, in {next_pass['minutes_from_now']:.0f} min)."
            )
    elif next_pass and next_pass["minutes_from_now"] <= 90:
        mode = "pass_opening_soon"
        line = (
            f"Pass window opening soon — {next_pass['sat_label']} over {site} "
            f"~{next_pass['culmination_utc'][11:16]} UTC "
            f"(in {next_pass['minutes_from_now']:.0f} min, elev {next_pass['elev_deg']}°)."
        )
    elif next_pass:
        mode = "quiet_until_pass"
        hours = next_pass["minutes_from_now"] / 60.0
        line = (
            f"Quiet because no useful pass until ~{next_pass['culmination_utc'][11:16]} UTC "
            f"({next_pass['sat_label']} over {site}, ~{hours:.1f} h, elev {next_pass['elev_deg']}°)."
        )
    elif last_pass:
        mode = "past_window_only"
        ago_h = -last_pass["minutes_from_now"] / 60.0
        line = (
            f"Last useful pass was {ago_h:.1f} h ago "
            f"({last_pass['sat_label']} {site}); none ahead in this window."
        )

    return {
        "site": site,
        "mode": mode,
        "line": line,
        "last_pass": last_pass,
        "next_pass": next_pass,
        "firms_latest_obs_utc": firms_latest_obs_utc,
        "as_of_utc": now.isoformat(),
    }


def render_figure(calendar: dict, statuses: list[dict], output_path: Path) -> Path:
    import matplotlib.pyplot as plt

    try:
        import scientific_map as sm

        fig_bg, ax_bg, text, muted, cyan, amber, grid = (
            sm.FIG_BG,
            sm.AX_BG,
            sm.TEXT,
            sm.MUTED,
            sm.CYAN,
            sm.AMBER,
            sm.GRID,
        )
    except Exception:  # noqa: BLE001
        fig_bg, ax_bg, text, muted, cyan, amber, grid = (
            "#080c16",
            "#0f172a",
            "#f8fafc",
            "#94a3b8",
            "#22d3ee",
            "#f59e0b",
            "#334155",
        )

    now = datetime.fromisoformat(calendar["generated_at_utc"])
    sat_order = list(SATELLITES.keys())
    site_colors = {"wales": cyan, "gower": amber}

    fig = plt.figure(figsize=(16, 9), dpi=160, facecolor=fig_bg)
    ax = fig.add_axes([0.08, 0.14, 0.84, 0.68])
    ax.set_facecolor(ax_bg)
    for spine in ax.spines.values():
        spine.set_color(grid)

    y_map = {label: i for i, label in enumerate(sat_order)}
    for p in calendar.get("passes", []):
        t = datetime.fromisoformat(p["culmination_utc"])
        hours = (t - now).total_seconds() / 3600.0
        y = y_map[p["sat_label"]]
        color = site_colors.get(p["site"], text)
        marker = "o" if p["site"] == "wales" else "D"
        size = 40 + min(80, max(0.0, p["elev_deg"]) * 2.5)
        ax.scatter(hours, y, s=size, color=color, marker=marker, edgecolors=text, linewidths=0.4, zorder=3, alpha=0.9)

    ax.axvline(0.0, color=text, linewidth=1.2, alpha=0.7, zorder=2)
    ax.set_yticks(list(y_map.values()))
    ax.set_yticklabels(list(y_map.keys()), color=text, fontsize=11)
    ax.set_xlabel("Hours from now (UTC)", color=muted, fontsize=10)
    ax.tick_params(colors=muted, labelsize=9)
    ax.grid(True, axis="x", color=grid, linewidth=0.6, alpha=0.7)
    ax.set_ylim(-0.7, len(sat_order) - 0.3)

    fig.text(0.08, 0.93, "Wales / Gower VIIRS pass calendar", color=text, fontsize=22, fontweight="bold")
    fig.text(
        0.08,
        0.885,
        f"As of {now.strftime('%d %b %Y %H:%M')} UTC · min elev {calendar['min_elev_deg']}° · "
        f"cyan = Wales · amber = Gower · marker size ~ elevation",
        color=muted,
        fontsize=9,
    )
    y = 0.07
    for st in statuses:
        fig.text(0.08, y, f"{st['site'].title()}: {st['line']}", color=cyan if st["site"] == "wales" else amber, fontsize=8.2)
        y -= 0.028
    fig.text(
        0.08,
        0.015,
        "TLE culminations via CelesTrak weather group + Skyfield. Not FIRMS acquisition times.",
        color=muted,
        fontsize=7.2,
    )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path.with_suffix(".png"), dpi=160, facecolor=fig_bg)
    fig.savefig(output_path.with_suffix(".svg"), facecolor=fig_bg)
    plt.close(fig)
    return output_path.with_suffix(".png")


def _read_firms_latest() -> str | None:
    summary = ROOT / "published" / "data" / "derived" / "summary.json"
    if not summary.exists():
        return None
    try:
        data = json.loads(summary.read_text())
        return data.get("latest_detection_utc")
    except Exception:  # noqa: BLE001
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="VIIRS overpass calendar for Wales / Gower")
    parser.add_argument("--hours-ahead", type=float, default=36.0)
    parser.add_argument("--hours-back", type=float, default=18.0)
    parser.add_argument("--min-elev", type=float, default=DEFAULT_MIN_ELEV_DEG)
    parser.add_argument("--sample-s", type=int, default=DEFAULT_SAMPLE_S)
    parser.add_argument("--figure", action="store_true", help="Write dark PNG/SVG timeline")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "published" / "local" / "pass-calendar",
    )
    parser.add_argument("--firms-latest", help="Override latest FIRMS obs UTC string")
    args = parser.parse_args()

    try:
        calendar = build_calendar(
            hours_ahead=args.hours_ahead,
            hours_back=args.hours_back,
            min_elev_deg=args.min_elev,
            sample_s=args.sample_s,
        )
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"error": f"{type(exc).__name__}: {exc}"}), flush=True)
        return 1

    firms_latest = args.firms_latest or _read_firms_latest()
    statuses = [
        status_message(calendar, site="wales", firms_latest_obs_utc=firms_latest),
        status_message(calendar, site="gower", firms_latest_obs_utc=firms_latest),
    ]
    calendar["status"] = statuses

    out_root = Path(args.output_root)
    out_root.mkdir(parents=True, exist_ok=True)
    json_path = out_root / "pass_calendar.json"
    json_path.write_text(json.dumps(calendar, indent=2) + "\n")

    print(json.dumps({"event": "PASS_CALENDAR", "path": str(json_path), "pass_count": calendar["pass_count"]}, indent=2))
    print()
    for st in statuses:
        print(f"[{st['mode']}] {st['line']}")
    print()
    print(f"{'when (UTC)':<22} {'site':<7} {'sat':<7} {'elev':>6} {'nadir_km':>8} {'min':>8}")
    for p in calendar["passes"]:
        when = p["culmination_utc"][:16].replace("T", " ")
        print(
            f"{when:<22} {p['site']:<7} {p['sat_label']:<7} {p['elev_deg']:>6.1f} "
            f"{p['nadir_km']:>8.0f} {p['minutes_from_now']:>8.1f}"
        )

    if args.figure:
        fig_path = render_figure(calendar, statuses, out_root / "figures" / "viirs_pass_calendar_dark")
        print(f"\nfigure: {fig_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
