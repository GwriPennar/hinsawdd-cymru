#!/usr/bin/env python3
"""Reproduce Project 004 data-centre direct-water scenarios.

This deliberately small standard-library script verifies the arithmetic in
``data/scenarios.csv``. It does not download sources or convert modelled
scenarios into measured observations.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
SCENARIO_PATH = PROJECT_DIR / "data" / "scenarios.csv"
TOLERANCE = 1e-6


@dataclass(frozen=True)
class Scenario:
    scope: str
    name: str
    capacity_mw: float
    load_factor: float
    wue_l_per_kwh: float
    expected_water_ml_per_day: float
    comparison_supply_ml_per_day: float
    expected_share_percent: float
    status: str

    @property
    def water_ml_per_day(self) -> float:
        litres_per_day = (
            self.capacity_mw
            * 1_000.0
            * self.load_factor
            * 24.0
            * self.wue_l_per_kwh
        )
        return litres_per_day / 1_000_000.0

    @property
    def share_percent(self) -> float:
        return self.water_ml_per_day / self.comparison_supply_ml_per_day * 100.0


def load_scenarios(path: Path = SCENARIO_PATH) -> list[Scenario]:
    scenarios: list[Scenario] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            scenarios.append(
                Scenario(
                    scope=row["scope"],
                    name=row["scenario"],
                    capacity_mw=float(row["capacity_mw"]),
                    load_factor=float(row["load_factor"]),
                    wue_l_per_kwh=float(row["wue_l_per_kwh"]),
                    expected_water_ml_per_day=float(row["water_ml_per_day"]),
                    comparison_supply_ml_per_day=float(
                        row["comparison_supply_ml_per_day"]
                    ),
                    expected_share_percent=float(row["share_percent"]),
                    status=row["status"],
                )
            )
    return scenarios


def verify(scenarios: list[Scenario]) -> None:
    for scenario in scenarios:
        water_error = abs(
            scenario.water_ml_per_day - scenario.expected_water_ml_per_day
        )
        share_error = abs(scenario.share_percent - scenario.expected_share_percent)
        if water_error > TOLERANCE or share_error > TOLERANCE:
            raise AssertionError(
                f"Scenario mismatch: {scenario.scope}/{scenario.name}: "
                f"water={scenario.water_ml_per_day:.6f}, "
                f"share={scenario.share_percent:.6f}%"
            )


def main() -> None:
    scenarios = load_scenarios()
    verify(scenarios)
    print("scope,scenario,water_ml_per_day,share_percent,status")
    for scenario in scenarios:
        print(
            f"{scenario.scope},{scenario.name},"
            f"{scenario.water_ml_per_day:.6f},"
            f"{scenario.share_percent:.6f},{scenario.status}"
        )


if __name__ == "__main__":
    main()
