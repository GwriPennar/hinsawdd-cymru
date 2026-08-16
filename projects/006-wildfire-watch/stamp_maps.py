"""Add an unmistakable UTC data stamp to Project 006 published PNG maps."""
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _label(summary: dict) -> tuple[str, str]:
    generated = _dt(str(summary["generated_at_utc"]))
    latest = _dt(str(summary["latest_detection_utc"]))
    label = (
        f"DATA SNAPSHOT {generated:%d %b %Y %H:%M UTC}   |   "
        f"LATEST OBSERVATION {latest:%d %b %Y %H:%M UTC}"
    ).upper()
    return label, generated.strftime("%Y-%m-%d_%H%MUTC")


def _font(size: int):
    for name in ("DejaVuSans-Bold.ttf", "Arial Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def stamp_png(path: Path, label: str, dated_path: Path) -> None:
    image = Image.open(path).convert("RGB")
    bar_height = max(54, round(image.height * 0.06))
    canvas = Image.new("RGB", (image.width, image.height + bar_height), (8, 12, 22))
    canvas.paste(image, (0, bar_height))
    draw = ImageDraw.Draw(canvas)
    font = _font(max(14, round(bar_height * 0.34)))
    bbox = draw.textbbox((0, 0), label, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text(
        ((image.width - text_w) / 2, (bar_height - text_h) / 2 - bbox[1]),
        label,
        font=font,
        fill=(248, 250, 252),
    )
    canvas.save(path, format="PNG", optimize=True)
    canvas.save(dated_path, format="PNG", optimize=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=ROOT)
    args = parser.parse_args()

    output_root = Path(args.output_root)
    summary = json.loads((output_root / "data" / "derived" / "summary.json").read_text())
    label, stamp = _label(summary)
    figures = output_root / "figures"

    stamped = []
    for stem in ("wales_wildfire_watch", "wales_firms_pixels"):
        for suffix in ("", "_square"):
            png = figures / f"{stem}_dark{suffix}.png"
            if not png.exists():
                continue
            dated_png = figures / f"{stem}_{stamp}_dark{suffix}.png"
            stamp_png(png, label, dated_png)
            stamped.append(str(png))

            svg = figures / f"{stem}_dark{suffix}.svg"
            if svg.exists():
                shutil.copyfile(svg, figures / f"{stem}_{stamp}_dark{suffix}.svg")

    print(json.dumps({"snapshot_stamp": stamp, "label": label, "stamped": stamped}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
