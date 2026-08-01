# Hinsawdd Cymru

**Data agored, dadansoddiad tryloyw, ffeithiau am hinsawdd Cymru.**

Open and reproducible analysis of public weather and climate data for Wales.

Hinsawdd Cymru is a small, public-facing research repository. Each numbered project asks a specific question, retains its source and derived data, documents every assumption, and produces a result that can be checked independently.

The repository distinguishes between:

- values published by an authoritative source;
- calculations derived in this repository;
- provisional scenarios that have not yet been published officially.

## Project registry

| ID | Project | Status | Main result |
|---|---|---|---|
| [001](projects/001-rolling-temperature/) | Wales August-to-July mean temperature | Provisional, independently revalidated | The 12 months ending July 2026 are robustly the warmest equivalent August-to-July period under every scenario tested. |

## Repository structure

```text
hinsawdd-cymru/
├── README.md
├── pyproject.toml
└── projects/
    └── 001-rolling-temperature/
        ├── README.md
        ├── METHODOLOGY.md
        ├── VALIDATION.md
        ├── analysis.py
        ├── fetch_source.py
        ├── verify.py
        ├── data/
        │   ├── raw/
        │   └── derived/
        ├── figures/
        └── tests/
```

Each project is self-contained, while the Python environment is shared at repository level.

## Reproduce Project 001

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python projects/001-rolling-temperature/analysis.py
pytest
```

## Quality approach

Project 001 uses a lightweight Reproducible Analytical Pipeline:

- immutable source snapshots with SHA-256 provenance;
- automatic reconciliation against the official annual column;
- a separate standard-library verification implementation;
- generated machine-readable outputs and public documentation;
- GitHub Actions validation on every change.

## Sources and licensing

Project 001 uses the Met Office HadUK-Grid Wales areal mean-temperature series, made available under the Open Government Licence. The source data remain subject to their original licence and Crown copyright.

The analysis code is released under the [MIT License](LICENSE).

## Independence

This is an independent project and is not an official Met Office product. Derived results should be described as calculations from Met Office data, not as figures published or endorsed by the Met Office.
