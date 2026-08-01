# Hinsawdd Cymru

**Data agored, dadansoddiad tryloyw, ffeithiau am hinsawdd Cymru.**

Open and reproducible analysis of public weather and climate data for Wales.

Hinsawdd Cymru is a small, public-facing research repository. Each numbered project asks a specific question, retains its source and derived data, documents every assumption, and produces a result that can be checked independently.

The repository is deliberately neutral. It distinguishes between:

- values published by an authoritative source;
- calculations derived in this repository;
- provisional estimates or scenarios that have not yet been published officially.

## Project registry

| ID | Project | Status | Main result |
|---|---|---|---|
| [001](projects/001-rolling-temperature/) | Wales August-to-July mean temperature | Provisional | The 12 months ending July 2026 are calculated to be the warmest August-to-July period in the Wales series, under every July scenario tested. |

## Repository structure

```text
hinsawdd-cymru/
├── README.md
├── pyproject.toml
└── projects/
    └── 001-rolling-temperature/
        ├── README.md
        ├── analysis.py
        ├── data/
        │   ├── raw/
        │   └── derived/
        ├── figures/
        └── tests/
```

Each project is self-contained, while the Python environment is shared at repository level.

## Reproduce the analysis

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python projects/001-rolling-temperature/analysis.py
pytest
```

To download the latest Met Office Wales series before running:

```bash
python projects/001-rolling-temperature/analysis.py --refresh
```

## Sources and licensing

Project 001 uses the Met Office HadUK-Grid Wales areal mean-temperature series, which is made available under the Open Government Licence. Source attribution and the retained snapshot date are recorded within the project.

The analysis code is released under the [MIT License](LICENSE). Source datasets remain subject to their original licences.

## Independence

This is an independent project and is not an official Met Office product. Derived results should be described as calculations from Met Office data, not as figures published or endorsed by the Met Office.
