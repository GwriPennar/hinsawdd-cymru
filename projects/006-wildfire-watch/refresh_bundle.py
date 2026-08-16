"""Build one HTML page that gathers the latest Project 006 refresh assets.

  python projects/006-wildfire-watch/refresh_bundle.py
  python projects/006-wildfire-watch/refresh_bundle.py --open

Writes:
  published/local/refresh/<stamp>/index.html
  published/local/refresh/latest/index.html
  published/local/run_all.html   (redirect to latest)
"""
from __future__ import annotations

import argparse
import html
import json
import os
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runs_index import INDEX_PATH, PUBLISHED, ROOT, build_index

REFRESH_ROOT = PUBLISHED / "local" / "refresh"
STABLE_POINTER = PUBLISHED / "local" / "run_all.html"

# Preferred section order for the all-in-one page
SECTION_ORDER = (
    "wales-publication",
    "swansea-gower-watch",
    "wales-now",
    "viirs-browse",
)

# Aliases produced by run_all.py (exclude older experiment aliases like viirs-full)
REFRESH_ALIASES = frozenset({"wales-map", "gower-watch", "wales-now", "viirs-simple"})


def _esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def _rel_from(html_dir: Path, target: Path | None) -> str | None:
    if target is None or not target.exists():
        return None
    return Path(os.path.relpath(Path(target).resolve(), html_dir.resolve())).as_posix()


def _path_from_artifact(rel: str | None) -> Path | None:
    if not rel:
        return None
    # Artifacts are stored relative to repo root or project root.
    for base in (ROOT.parent.parent, ROOT, Path.cwd()):
        cand = (base / rel).resolve()
        if cand.exists():
            return cand
    # Also try stripping a leading "projects/006-wildfire-watch/"
    if rel.startswith("projects/006-wildfire-watch/"):
        cand = (ROOT / rel.split("projects/006-wildfire-watch/", 1)[1]).resolve()
        if cand.exists():
            return cand
    # Paths already under published/
    cand = (ROOT / rel).resolve() if not Path(rel).is_absolute() else Path(rel)
    if cand.exists():
        return cand
    # Artifact strings in index are like "published/..." relative to project ROOT
    if rel.startswith("published/"):
        cand = (ROOT / rel).resolve()
        if cand.exists():
            return cand
    return None


def _images_for_run(run: dict[str, Any], html_dir: Path) -> list[tuple[str, str]]:
    """Return (caption, relative_url) image pairs for a run."""
    arts = run.get("artifacts") or {}
    kind = run.get("kind")
    out: list[tuple[str, str]] = []

    def add(caption: str, rel_or_path: str | Path | None) -> None:
        if rel_or_path is None:
            return
        path = _path_from_artifact(str(rel_or_path)) if not isinstance(rel_or_path, Path) else rel_or_path
        href = _rel_from(html_dir, path)
        if href:
            out.append((caption, href))

    if kind == "wales-publication":
        add("Cluster map", arts.get("cluster_map"))
        add("Pixel map", arts.get("pixel_map"))
    elif kind == "swansea-gower-watch":
        add("Gower FIRMS map", arts.get("map"))
        bbox = PUBLISHED / "local" / "swansea-gower" / "figures" / "swansea_gower_watch_bbox_dark.png"
        add("Watch bbox", bbox)
    elif kind == "wales-now":
        add("Wales now pixels", arts.get("map"))
    elif kind == "viirs-browse":
        add("Contact sheet", arts.get("contact_sheet"))
        # Individual explained frames
        stamp = _path_from_artifact(str(run.get("path") or ""))
        if stamp:
            manifest = {}
            mpath = stamp / "manifest.json"
            if mpath.exists():
                try:
                    manifest = json.loads(mpath.read_text())
                except json.JSONDecodeError:
                    manifest = {}
            for fig in manifest.get("explained_figures") or []:
                add(Path(str(fig)).stem.replace("_", " "), stamp / str(fig))

    return out


def _links_for_run(run: dict[str, Any], html_dir: Path) -> list[tuple[str, str]]:
    arts = run.get("artifacts") or {}
    links: list[tuple[str, str]] = []

    def add(label: str, rel: str | None) -> None:
        path = _path_from_artifact(rel)
        href = _rel_from(html_dir, path)
        if href:
            links.append((label, href))

    if run.get("kind") == "wales-publication":
        add("Leaflet site", arts.get("site"))
        add("Summary JSON", arts.get("summary"))
    if run.get("kind") == "viirs-browse":
        add("VIIRS review.html", arts.get("review_html"))
        add("Explainers", arts.get("explainers"))
        add("Manifest", arts.get("manifest"))
    if run.get("kind") == "swansea-gower-watch":
        add("Detections CSV", arts.get("detections"))
        add("Summary JSON", arts.get("summary"))
    if run.get("kind") == "wales-now":
        add("Pixels CSV", arts.get("pixels"))
        add("Scan estimates", arts.get("scan_estimates"))
    return links


def _stats_lines(run: dict[str, Any]) -> list[str]:
    stats = run.get("stats")
    lines: list[str] = []
    if isinstance(stats, dict):
        for key, value in stats.items():
            if value is None or key in {"estimates", "error"}:
                continue
            if isinstance(value, (list, dict)):
                value = json.dumps(value, separators=(",", ":"))
            lines.append(f"{key}: {value}")
    if run.get("latest_obs_utc"):
        lines.insert(0, f"latest_obs_utc: {run['latest_obs_utc']}")
    if run.get("time_date"):
        lines.insert(0, f"gibs_date: {run['time_date']}")
    return lines


def render_html(index: dict[str, Any], *, stamp: str, html_dir: Path) -> str:
    current = [
        r
        for r in index["runs"]
        if r.get("latest_for_alias", True)
        and str(r.get("base_alias") or r.get("alias")) in REFRESH_ALIASES
    ]
    by_kind = {k: [] for k in SECTION_ORDER}
    other: list[dict[str, Any]] = []
    for r in current:
        kind = str(r.get("kind") or "")
        if kind in by_kind:
            by_kind[kind].append(r)
        else:
            other.append(r)

    sections: list[dict[str, Any]] = []
    for kind in SECTION_ORDER:
        sections.extend(by_kind[kind])
    sections.extend(other)

    generated = index.get("generated_at_utc") or datetime.now(timezone.utc).isoformat()
    toc_bits = []
    body_bits = []
    for r in sections:
        anchor = _esc(r.get("alias") or r.get("run_id"))
        toc_bits.append(f'<a href="#{anchor}">{_esc(r.get("name"))}</a>')

        imgs = _images_for_run(r, html_dir)
        links = _links_for_run(r, html_dir)
        stats = _stats_lines(r)

        img_html = ""
        for caption, href in imgs:
            img_html += (
                f'<figure class="media">'
                f'<img src="{_esc(href)}" alt="{_esc(caption)}" loading="lazy">'
                f"<figcaption>{_esc(caption)}</figcaption>"
                f"</figure>\n"
            )
        if not img_html:
            img_html = '<p class="missing">No preview images found for this run.</p>'

        link_html = ""
        if links:
            items = "".join(f'<li><a href="{_esc(href)}">{_esc(label)}</a></li>' for label, href in links)
            link_html = f'<ul class="links">{items}</ul>'

        stats_html = ""
        if stats:
            stats_html = "<ul class='stats'>" + "".join(f"<li><code>{_esc(s)}</code></li>" for s in stats) + "</ul>"

        when = str(r.get("generated_at_utc") or "")[:19]
        body_bits.append(
            f"""
<section class="card" id="{anchor}">
  <h2>{_esc(r.get("name"))} <span class="alias">({_esc(r.get("alias"))})</span></h2>
  <p class="meta"><code>{_esc(r.get("run_id"))}</code> · {_esc(when)} UTC · {_esc(r.get("kind"))}</p>
  <p class="desc">{_esc(r.get("description") or r.get("label"))}</p>
  {stats_html}
  {link_html}
  <div class="gallery">{img_html}</div>
</section>
"""
        )

    toc = " · ".join(toc_bits)
    body = "\n".join(body_bits)
    footer = "Generated by <code>refresh_bundle.py</code>"
    try:
        footer += f" · index <code>{_esc(INDEX_PATH.resolve().relative_to(ROOT.resolve()).as_posix())}</code>"
    except ValueError:
        footer += f" · index <code>{_esc(INDEX_PATH)}</code>"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Project 006 full refresh — {_esc(stamp)}</title>
<style>
  :root {{
    --bg: #080c16;
    --card: #0f172a;
    --text: #f8fafc;
    --muted: #94a3b8;
    --line: #334155;
    --accent: #22d3ee;
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
    padding: 14px 18px;
    background: rgba(8,12,22,0.94);
    border-bottom: 1px solid var(--line);
    backdrop-filter: blur(8px);
  }}
  .topbar h1 {{ margin: 0; font-size: 1.15rem; font-weight: 650; }}
  .topbar p {{ margin: 4px 0 0; color: var(--muted); font-size: 0.88rem; }}
  main {{ max-width: 1100px; margin: 0 auto; padding: 18px 16px 80px; }}
  .toc {{
    margin: 0 0 22px; padding: 12px 14px;
    border: 1px dashed var(--line); border-radius: 10px;
    color: var(--muted); font-size: 0.92rem;
  }}
  .toc a {{ color: var(--accent); text-decoration: none; margin-right: 4px; }}
  .toc a:hover {{ text-decoration: underline; }}
  .card {{
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 16px;
    margin: 0 0 24px;
  }}
  .card h2 {{ margin: 0 0 6px; font-size: 1.2rem; }}
  .alias {{ color: var(--muted); font-weight: 500; font-size: 0.95rem; }}
  .meta {{ color: var(--muted); font-size: 0.82rem; margin: 0 0 8px; }}
  .desc {{ margin: 0 0 12px; color: #cbd5e1; }}
  .stats, .links {{ margin: 0 0 12px; padding-left: 1.1rem; color: var(--muted); }}
  .stats code, code {{ color: #a5f3fc; font-size: 0.86rem; }}
  .links a {{ color: var(--accent); }}
  .gallery {{ display: grid; gap: 14px; }}
  .media {{
    margin: 0;
    background: #020617;
    border: 1px solid var(--line);
    border-radius: 8px;
    overflow: hidden;
  }}
  .media img {{ display: block; width: 100%; height: auto; }}
  .media figcaption {{
    padding: 8px 10px; color: var(--muted); font-size: 0.82rem;
    border-top: 1px solid var(--line);
  }}
  .missing {{ color: var(--muted); }}
  .note {{
    margin: 0 0 18px; padding: 12px 14px;
    border-left: 3px solid var(--accent);
    background: #0b1220; color: var(--muted); font-size: 0.9rem;
  }}
  footer {{ color: var(--muted); font-size: 0.8rem; margin-top: 28px; }}
</style>
</head>
<body>
<header class="topbar">
  <h1>Project 006 — full refresh</h1>
  <p>Stamp <code>{_esc(stamp)}</code> · index {_esc(str(generated)[:19])} UTC · satellite thermal anomalies are not confirmed wildfires</p>
</header>
<main>
  <p class="note">
    One page for the latest of each run after data collection and asset creation.
    Historical stamps stay in the runs index; this page only shows current aliases.
  </p>
  <nav class="toc"><strong>Jump:</strong> {toc}</nav>
  {body}
  <footer>
    {footer}
  </footer>
</main>
</body>
</html>
"""


def write_refresh_bundle(index: dict[str, Any] | None = None, *, stamp: str | None = None) -> dict[str, Any]:
    index = index or build_index()
    stamp = stamp or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stamp_dir = REFRESH_ROOT / stamp
    latest_dir = REFRESH_ROOT / "latest"
    stamp_dir.mkdir(parents=True, exist_ok=True)
    latest_dir.mkdir(parents=True, exist_ok=True)

    html_text = render_html(index, stamp=stamp, html_dir=stamp_dir)
    stamp_path = stamp_dir / "index.html"
    stamp_path.write_text(html_text)

    # Rewrite latest with paths relative to latest/
    latest_html = render_html(index, stamp=stamp, html_dir=latest_dir)
    latest_path = latest_dir / "index.html"
    latest_path.write_text(latest_html)

    STABLE_POINTER.parent.mkdir(parents=True, exist_ok=True)
    STABLE_POINTER.write_text(
        "<!DOCTYPE html><meta charset='utf-8'>"
        "<meta http-equiv='refresh' content='0; url=refresh/latest/index.html'>"
        "<title>Project 006 full refresh</title>"
        "<p><a href='refresh/latest/index.html'>Open full refresh</a></p>\n"
    )

    def _rel_meta(path: Path) -> str:
        try:
            return str(path.resolve().relative_to(ROOT.resolve()))
        except ValueError:
            return str(path)

    # Keep a machine-readable sidecar next to latest
    meta = {
        "stamp": stamp,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "index_generated_at_utc": index.get("generated_at_utc"),
        "html": _rel_meta(stamp_path),
        "latest_html": _rel_meta(latest_path),
        "pointer": _rel_meta(STABLE_POINTER),
        "runs": [
            {
                "name": r.get("name"),
                "alias": r.get("alias"),
                "run_id": r.get("run_id"),
                "kind": r.get("kind"),
            }
            for r in index["runs"]
            if r.get("latest_for_alias", True)
            and str(r.get("base_alias") or r.get("alias")) in REFRESH_ALIASES
        ],
    }
    (stamp_dir / "bundle.json").write_text(json.dumps(meta, indent=2) + "\n")
    (latest_dir / "bundle.json").write_text(json.dumps(meta, indent=2) + "\n")

    # Also refresh runs_index.json so the HTML is discoverable
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(index, indent=2) + "\n")

    return meta


def main() -> None:
    parser = argparse.ArgumentParser(description="Write the Project 006 all-in-one refresh HTML")
    parser.add_argument("--open", action="store_true", help="Open the latest HTML in a browser")
    parser.add_argument("--stamp", help="Optional stamp id YYYYMMDDTHHMMSSZ")
    args = parser.parse_args()
    meta = write_refresh_bundle(stamp=args.stamp)
    print(json.dumps(meta, indent=2))
    if args.open:
        webbrowser.open((REFRESH_ROOT / "latest" / "index.html").resolve().as_uri())


if __name__ == "__main__":
    main()
