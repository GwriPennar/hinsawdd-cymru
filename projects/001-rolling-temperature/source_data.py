"""Source parsing and provenance for Project 001."""
from __future__ import annotations
import calendar, hashlib, json, re
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
import pandas as pd

MONTHS = "jan feb mar apr may jun jul aug sep oct nov dec".split()
PROJECT_DIR = Path(__file__).resolve().parent
RAW_DIR = PROJECT_DIR / "data/raw"
LEGACY_SOURCE = RAW_DIR / "wales_tmean_monthly_2026-07-01.txt"
LAST_UPDATED_RE = re.compile(r"^(?:Last updated|Source last updated:)\s*(.+)$", re.MULTILINE)

@dataclass(frozen=True)
class SourceBundle:
    path: Path
    monthly: pd.DataFrame
    annual: pd.DataFrame
    source_last_updated: str | None
    snapshot_kind: str
    manifest: dict[str, object] | None

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def latest_source_path() -> Path:
    exact = sorted([*RAW_DIR.glob("metoffice-wales-tmean-source-*.txt"), *RAW_DIR.glob("metoffice-wales-tmean-retrieved-*.txt")])
    if exact:
        return exact[-1]
    if LEGACY_SOURCE.exists():
        return LEGACY_SOURCE
    raise FileNotFoundError("No Met Office source snapshot is available")

def _manifest(path: Path) -> dict[str, object] | None:
    manifest_path = path.with_suffix(".provenance.json")
    if not manifest_path.exists():
        return None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("sha256") != sha256(path):
        raise ValueError(f"Source hash does not match {manifest_path}")
    return manifest

def _parse_wide(text: str) -> pd.DataFrame:
    lines = text.splitlines()
    header_index = next((i for i, line in enumerate(lines) if line.strip().lower().startswith("year")), None)
    if header_index is None:
        raise ValueError("Could not find source header")
    header_line = lines[header_index]
    matches = list(re.finditer(r"\S+", header_line))
    names = [match.group(0) for match in matches]
    if "ann" not in names:
        return pd.read_csv(StringIO("\n".join(lines[header_index:])), sep=r"\s+", na_values=["NaN", "---"])
    ends = [match.end() for match in matches]
    spans = [(0 if i == 0 else ends[i - 1], ends[i]) for i in range(len(ends))]
    rows = []
    for raw in lines[header_index + 1:]:
        fields = [raw[start:end].strip() for start, end in spans]
        if fields and fields[0].lstrip("-").isdigit():
            rows.append(fields)
    wide = pd.DataFrame(rows, columns=names).replace({"": pd.NA, "NaN": pd.NA, "---": pd.NA})
    for name in names:
        wide[name] = pd.to_numeric(wide[name], errors="coerce")
    return wide

def load_source(path: Path | None = None) -> SourceBundle:
    source_path = path or latest_source_path()
    text = source_path.read_text(encoding="utf-8")
    wide = _parse_wide(text)
    missing = {"year", *MONTHS}.difference(wide.columns)
    if missing:
        raise ValueError(f"Missing source columns: {sorted(missing)}")
    records = []
    for row in wide.itertuples(index=False):
        year = int(row.year)
        for month, name in enumerate(MONTHS, 1):
            value = getattr(row, name)
            if pd.notna(value):
                records.append({"date": pd.Timestamp(year, month, 1), "year": year, "month": month,
                    "mean_temperature_c": float(value), "days": calendar.monthrange(year, month)[1],
                    "status": "published_monthly_series"})
    monthly = pd.DataFrame(records).sort_values("date").reset_index(drop=True)
    if monthly.empty or monthly["date"].duplicated().any():
        raise ValueError("Empty or duplicate monthly series")
    expected = pd.date_range(monthly.iloc[0]["date"], monthly.iloc[-1]["date"], freq="MS")
    if not expected.equals(pd.DatetimeIndex(monthly["date"])):
        raise ValueError("Unexpected gap in monthly series")
    annual = pd.DataFrame(columns=["year", "official_annual_mean_c"])
    if "ann" in wide.columns:
        annual = (wide.loc[wide["ann"].notna(), ["year", "ann"]]
            .rename(columns={"ann": "official_annual_mean_c"})
            .astype({"year": int, "official_annual_mean_c": float}).reset_index(drop=True))
    match = LAST_UPDATED_RE.search(text)
    manifest = _manifest(source_path)
    kind = "exact_upstream_snapshot" if manifest and manifest.get("exact_upstream_bytes") is True else "legacy_normalized_snapshot"
    return SourceBundle(source_path, monthly, annual, match.group(1).strip() if match else None, kind, manifest)
