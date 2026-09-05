#!/usr/bin/env python3
"""Offline structural checks for Project 009, not scientific validation."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
ACCESS = {"relevant_sections", "abstract_only", "abstract_and_data_statement", "metadata_abstract_and_supplied_figures", "metadata_only"}
ASSESSMENTS = {"supported", "not_established", "disputed", "not_demonstrated", "inconsistent_with_assessed_evidence", "contradicted", "unsupported_by_supplied_evidence", "overstatement"}
DATA_STATUS = {"not_acquired", "product_selection_pending", "acquired"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def valid_url(value: str) -> bool:
    parsed = urlsplit(value)
    return parsed.scheme == "https" and bool(parsed.netloc) and not any(c.isspace() for c in value)


def load_register(root: Path, name: str, key: str) -> tuple[dict, list[dict]]:
    obj = json.loads((root / name).read_text(encoding="utf-8"))
    require(obj.get("schema_version") == 1, f"{name}: unsupported schema")
    date.fromisoformat(obj["review_date"])
    rows = obj[key]
    require(isinstance(rows, list) and bool(rows), f"{name}: empty or invalid register")
    return obj, rows


def validate(root: Path = ROOT) -> dict:
    registers = [load_register(root, *args) for args in (("sources.json", "sources"), ("claims.json", "claims"), ("datasets.json", "datasets"))]
    require(len({r[0]["review_date"] for r in registers}) == 1, "Register review dates disagree")
    review_date = registers[0][0]["review_date"]
    sources, claims, datasets = [r[1] for r in registers]
    for rows, prefix in ((sources, "S"), (claims, "C"), (datasets, "D")):
        ids = [r["id"] for r in rows]
        require(len(ids) == len(set(ids)), f"Duplicate {prefix} identifiers")
        require(all(re.fullmatch(prefix + r"\d{2}", x) for x in ids), f"Invalid {prefix} identifier")
    source_ids = {s["id"] for s in sources}
    dois = []
    for source in sources:
        for field in ("authors", "title", "url", "kind", "locator", "role", "note"):
            require(isinstance(source.get(field), str) and bool(source[field].strip()), f"{source['id']}: missing {field}")
        require(source.get("access") in ACCESS, f"{source['id']}: invalid access")
        require(valid_url(source["url"]), f"{source['id']}: invalid URL")
        require(isinstance(source.get("year"), int) and 1600 <= source["year"] <= date.fromisoformat(review_date).year, f"{source['id']}: invalid year")
        if "alternate_url" in source:
            require(valid_url(source["alternate_url"]), f"{source['id']}: invalid alternate URL")
        if "doi" in source:
            require(re.fullmatch(r"10\.\d{4,9}/\S+", source["doi"]) is not None, f"{source['id']}: invalid DOI")
            dois.append(source["doi"].lower())
    require(len(dois) == len(set(dois)), "Duplicate DOI entries")
    for row in claims + datasets:
        refs = row.get("sources")
        require(isinstance(refs, list) and bool(refs), f"{row['id']}: no sources")
        require(set(refs) <= source_ids, f"{row['id']}: unknown source")
    for claim in claims:
        require(claim.get("assessment") in ASSESSMENTS, f"{claim['id']}: invalid assessment")
        for field in ("claim", "scope", "next_test"):
            require(isinstance(claim.get(field), str) and bool(claim[field].strip()), f"{claim['id']}: missing {field}")
    for dataset in datasets:
        require(dataset.get("status") in DATA_STATUS, f"{dataset['id']}: invalid dataset status")
        for field in ("name", "units", "measurement_class", "purpose"):
            require(isinstance(dataset.get(field), str) and bool(dataset[field].strip()), f"{dataset['id']}: missing {field}")
        if dataset["status"] == "acquired":
            for field in ("path", "sha256", "retrieved_at", "licence", "version"):
                require(bool(dataset.get(field)), f"{dataset['id']}: acquired without {field}")
            raw = (root / dataset["path"]).resolve()
            require(raw.is_relative_to(root.resolve()), "Dataset path escapes project")
            require(raw.is_file(), f"{dataset['id']}: acquired file missing")
            require(hashlib.sha256(raw.read_bytes()).hexdigest() == dataset["sha256"], f"{dataset['id']}: checksum mismatch")
    for path in root.glob("*.md"):
        citations = set(re.findall(r"\bS\d{2}\b", path.read_text(encoding="utf-8")))
        require(citations <= source_ids, f"{path.name}: unknown citation {citations - source_ids}")
    files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.glob("*.json"))}
    return {"status": "passed", "scope": "offline_register_integrity_not_scientific_verification", "review_date": review_date, "sources": len(sources), "claims": len(claims), "datasets": len(datasets), "acquired_datasets": sum(d["status"] == "acquired" for d in datasets), "register_sha256": files}


def catalogue(root: Path = ROOT) -> str:
    _, sources = load_register(root, "sources.json", "sources")
    lines = ["# Project 009 source catalogue", "", "Generated from sources.json. Access level is not a quality score or a vote.", ""]
    for s in sources:
        lines.extend([f"## {s['id']}: {s['title']}", "", f"{s['authors']} ({s['year']}). Type: {s['kind']}. Access: {s['access']}.", "", s["url"], "", f"Locator: {s['locator']}", "", s["note"], ""])
        if "doi" in s:
            lines.extend([f"DOI: {s['doi']}", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--catalogue", type=Path)
    args = parser.parse_args()
    try:
        result = validate()
        text = json.dumps(result, indent=2) + "\n"
        for path, content in ((args.output, text), (args.catalogue, catalogue())):
            if path is not None:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
        print(text, end="")
        return 0
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(f"Validation failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
