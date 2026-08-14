"""Keep the Project 006 README publication status aligned with the published snapshot."""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
START = "<!-- PROJECT006_STATUS_START -->"
END = "<!-- PROJECT006_STATUS_END -->"


def _read_committed_summary() -> dict:
    path = "projects/006-wildfire-watch/published/data/derived/summary.json"
    result = subprocess.run(
        ["git", "show", f"HEAD:{path}"],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def _read_summary(state: str) -> dict:
    path = ROOT / "published" / "data" / "derived" / "summary.json"
    if state == "success" and path.exists():
        return json.loads(path.read_text())
    return _read_committed_summary()


def _display_time(value: str) -> str:
    if not value:
        return "unknown"
    dt = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    return dt.strftime("%d %B %Y %H:%M UTC")


def _stamp(value: str) -> str:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%d_%H%MUTC")


def _status_block(summary: dict, state: str, attempted_at: str) -> str:
    generated = str(summary.get("generated_at_utc", ""))
    latest = str(summary.get("latest_detection_utc", ""))
    detections = int(summary.get("wales_watch_detection_count", summary.get("detection_count", 0)) or 0)
    clusters = int(summary.get("official_wales_candidate_cluster_count", 0) or 0)
    stamp = _stamp(generated) if generated else "undated"
    attempt_text = _display_time(attempted_at)

    if state == "success":
        headline = "✅ **Latest refresh succeeded.**"
        attempt = f"Latest refresh attempt: **{attempt_text}**."
    else:
        headline = "⚠️ **Latest refresh failed; the previous successful publication is retained.**"
        attempt = (
            f"Latest refresh attempt: **{attempt_text}**, failed before publication. "
            "The current known failure mode is a NASA FIRMS connection error during the live VIIRS fetch."
        )

    return f"""{START}
> {headline}  
> Latest successful data snapshot: **{_display_time(generated)}**.  
> Latest satellite observation in that snapshot: **{_display_time(latest)}**.  
> Published Wales-window detections: **{detections:,}**. Derived candidate clusters inside the official Wales boundary: **{clusters}**.  
> {attempt}  
> Date-stamped map stem for this successful snapshot: `{stamp}`.
{END}"""


def update_readme(state: str, attempted_at: str) -> None:
    readme = ROOT / "README.md"
    text = readme.read_text()
    summary = _read_summary(state)
    block = _status_block(summary, state, attempted_at)

    if START in text and END in text:
        before, rest = text.split(START, 1)
        _, after = rest.split(END, 1)
        text = before + block + after
    else:
        marker = "## Latest published maps"
        text = text.replace(marker, block + "\n\n" + marker, 1)

    readme.write_text(text)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", choices=("success", "failure"), required=True)
    parser.add_argument("--attempted-at", default=datetime.now(timezone.utc).isoformat())
    args = parser.parse_args()
    update_readme(args.state, args.attempted_at)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
