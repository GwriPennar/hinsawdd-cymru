"""Download an immutable Met Office Wales rain-days source snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

SERIES_URL = "https://www.metoffice.gov.uk/pub/data/weather/uk/climate/datasets/Raindays1mm/date/Wales.txt"
EXPECTED_PREFIX = b"Areal values from HadUK-Grid 1km gridded climate data from land surface network"
EXPECTED_DESCRIPTION = (
    "Monthly, seasonal and annual number of days in the month with precipitation amount >= 1mm for Wales"
)
LAST_UPDATED_RE = re.compile(r"^Last updated\s+(.+)$", re.MULTILINE)


@dataclass(frozen=True)
class DownloadResult:
    source_path: Path
    manifest_path: Path
    sha256: str
    source_last_updated: str


def download_source(output_dir: Path, *, url: str = SERIES_URL) -> DownloadResult:
    """Fetch and preserve the exact official HTTP response bytes."""

    request = Request(url, headers={"User-Agent": "Hinsawdd-Cymru/0.4 (+public reproducible research)"})
    retrieved_at = datetime.now(timezone.utc).replace(microsecond=0)
    with urlopen(request, timeout=60) as response:  # noqa: S310 - fixed official HTTPS URL
        payload = response.read()
        status = getattr(response, "status", 200)
        content_type = response.headers.get("Content-Type")
        etag = response.headers.get("ETag")
        last_modified = response.headers.get("Last-Modified")

    if status != 200:
        raise RuntimeError(f"Unexpected HTTP status: {status}")
    if not payload.startswith(EXPECTED_PREFIX):
        raise ValueError("Downloaded content is not the expected Met Office Wales series")

    text = payload.decode("utf-8")
    required = (EXPECTED_DESCRIPTION, "Areal series, starting in 1891", "year", "ann")
    if any(item not in text for item in required):
        raise ValueError("Official rain-days source header is incomplete")

    match = LAST_UPDATED_RE.search(text)
    if match is None:
        raise ValueError("Could not parse the source Last updated field")
    source_last_updated = match.group(1).strip()

    output_dir.mkdir(parents=True, exist_ok=True)
    retrieval_token = retrieved_at.strftime("%Y-%m-%dT%H%M%SZ")
    stem = f"metoffice-wales-raindays1mm-retrieved-{retrieval_token}"
    source_path = output_dir / f"{stem}.txt"
    manifest_path = output_dir / f"{stem}.provenance.json"
    digest = hashlib.sha256(payload).hexdigest()

    if source_path.exists() and source_path.read_bytes() != payload:
        raise FileExistsError(f"Refusing to overwrite a different snapshot: {source_path}")
    source_path.write_bytes(payload)

    manifest = {
        "schema_version": 1,
        "source_url": url,
        "retrieved_at_utc": retrieved_at.isoformat().replace("+00:00", "Z"),
        "source_last_updated": source_last_updated,
        "http_status": status,
        "content_type": content_type,
        "etag": etag,
        "last_modified": last_modified,
        "byte_count": len(payload),
        "sha256": digest,
        "exact_upstream_bytes": True,
        "transformation": "none",
        "metric": "days with precipitation amount >= 1 mm",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return DownloadResult(source_path, manifest_path, digest, source_last_updated)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = download_source(args.output_dir)
    print(
        json.dumps(
            {
                "source_path": str(result.source_path),
                "manifest_path": str(result.manifest_path),
                "sha256": result.sha256,
                "source_last_updated": result.source_last_updated,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
