# Project 004 methodology

## Scope

Project 004 is a quantitative public-research project on water consumption in Wales, with a focused case study on data-centre demand.

It separates four concepts that are often conflated:

1. **public water supplied** by water companies;
2. **customer consumption** within public supply;
3. **leakage and other distribution-system uses/losses**;
4. **direct abstraction** outside public supply.

The data-centre model currently addresses **direct operational site water** only. It does not add indirect water consumed in electricity generation, semiconductor manufacturing, construction or the wider supply chain.

## Units

- `1 megalitre (Ml) = 1,000,000 litres`
- `1 MW = 1,000 kW`
- WUE is expressed as `litres per kWh of IT energy (L/kWh)`.

## Wales public-supply baseline

The primary national baseline is the Welsh Government Wellbeing of Wales 2025 publication:

- Dŵr Cymru Welsh Water + Hafren Dyfrdwy: approximately **920 Ml/d** in 2024–25;
- private water supplies: approximately **13.8 Ml/d**.

The 920 Ml/d value is used only as a present-day comparison denominator. It is not treated as total Welsh abstraction or total consumptive use.

Source:
https://www.gov.wales/wellbeing-wales-2025-resilient-wales-html

## Household and non-household boundary

The project uses regulatory categories rather than inventing an “industry” share.

`non-household` includes commercial and industrial customers as well as public and institutional customers. A household/non-household split therefore answers a different question from an economy-wide sectoral abstraction split.

The initial public summary retains a historical Dŵr Cymru regulatory split of approximately:

- household customer consumption: 534 Ml/d;
- non-household customer consumption: 166 Ml/d.

Normalising only these two customer-consumption components gives:

- household: `534 / (534 + 166) = 76.3%`;
- non-household: `166 / (534 + 166) = 23.7%`.

This is labelled historical/working because it is not the same reference year as the 920 Ml/d national baseline and because Ofwat later investigated Dŵr Cymru’s leakage and per-capita-consumption reporting.

No chart should imply that 76/24 is a fully reconciled 2024–25 all-Wales split until current APR tables for both Welsh suppliers are extracted and reconciled.

## Data-centre census boundary

A raw count of “data centres” is unstable because:

- there is no universally accepted formal definition;
- one campus can contain multiple data-centre buildings;
- directories can mix operational, planned and interconnection facilities;
- enterprise/private facilities are not fully captured in public colocation datasets.

Project 004 therefore uses two different evidence layers:

### Site-count layer

Senedd Research, July 2026:

- South Wales: at least 7 active data-centre sites;
- North Wales: 1 active site at St Asaph;
- multiple planned sites.

### Capacity layer

DSIT’s autumn-2024 estimate:

- Wales operational colocation maximum rated IT load: **154 MW**.

DSIT explicitly excludes enterprise data centres. This limitation is carried through the model rather than silently corrected by an invented uplift.

## Direct-water model

For a capacity `C` MW, average IT load factor `f`, and direct site WUE `w` L/kWh:

`daily litres = C × 1000 × f × 24 × w`

`daily Ml = daily litres / 1,000,000`

The share of the present Wales public-supply baseline is:

`share (%) = daily Ml / 920 × 100`

### Current scenarios

| Scenario | C | f | w |
|---|---:|---:|---:|
| Low-water | 154 MW | 0.50 | 0.10 L/kWh |
| Central | 154 MW | 0.65 | 0.30 L/kWh |
| High-water | 154 MW | 0.80 | 0.90 L/kWh |

Calculated values:

- Low: `154 × 1000 × 0.50 × 24 × 0.10 = 184,800 L/d = 0.1848 Ml/d`.
- Central: `154 × 1000 × 0.65 × 24 × 0.30 = 720,720 L/d = 0.72072 Ml/d`.
- High: `154 × 1000 × 0.80 × 24 × 0.90 = 2,661,120 L/d = 2.66112 Ml/d`.

Against 920 Ml/d:

- Low: 0.0201%.
- Central: 0.0783%.
- High: 0.2893%.

## Why these WUE scenarios are illustrative

The project deliberately avoids claiming one “Welsh WUE”. Cooling systems differ materially.

Published evidence includes:

- Microsoft fleet-wide average WUE of **0.27 L/kWh in 2025**;
- Microsoft’s next-generation closed-loop design, which can avoid ongoing water consumption for cooling after initial fill;
- Vantage CWL1’s published mix of indirect evaporative, dry-cooler and rack-level cooling technologies;
- academic literature showing that traditional evaporative cooling can be materially more water intensive.

The low/central/high values are therefore **scenario parameters**, not observations of the Welsh fleet. Their job is to expose sensitivity.

The central 0.30 L/kWh value is close to a current hyperscale fleet benchmark, not an assertion that every Welsh facility performs at that level.

## Future scenario

The UK Government says the South Wales AI Growth Zone could harness **over 1 GW** by the early 2030s. Project 004 uses exactly 1,000 MW as an illustrative round-number scenario, not as a forecast or a claim about delivered capacity.

At 1,000 MW:

- Low: 1.20 Ml/d.
- Central: 4.68 Ml/d.
- High: 17.28 Ml/d.

Relative to the *current* 920 Ml/d comparison baseline these are 0.13%, 0.51% and 1.88% respectively.

This comparison is intentionally labelled illustrative because future public-water supply, occupancy, cooling designs, climate conditions, reused-water availability and water-resource-zone constraints will differ.

## Local versus national impact

National percentage is not used as a proxy for local significance.

A data centre can represent a small fraction of Wales-wide supply yet still require network reinforcement or materially affect a constrained water-resource zone. Senedd Research records this issue explicitly for the planned Vantage CWL4 development in Bridgend.

Future facility-level work should therefore record:

- water resource zone;
- water company;
- potable/non-potable/reclaimed source;
- maximum daily demand where disclosed;
- average annual demand where disclosed;
- drought or peak-temperature operating mode;
- whether evaporative cooling is seasonal;
- any required network reinforcement.

## Drought context

NRW’s drought status is treated as environmental/hydrological context only. The project does not infer household restrictions from an NRW drought declaration.

## Evidence hierarchy

Preferred order:

1. Welsh Government, UK Government, NRW, Ofwat and other regulatory publications;
2. Senedd Research and parliamentary technical briefings;
3. operator technical disclosures and planning documents;
4. peer-reviewed research;
5. commercial directories only for discovery, never as the sole basis for a national total.

## Publication rules

The following wording rules are mandatory for Project 004 outputs:

- use **estimated** or **modelled** for the data-centre national total;
- never call non-household water “industry water” without a separate sectoral decomposition;
- never combine operational and planned capacity in the same “current” total;
- never describe 920 Ml/d as total Welsh water abstraction;
- distinguish direct site water from indirect electricity/supply-chain water;
- retain low/central/high sensitivity until measured Welsh facility data justify a narrower interval;
- state the reference year beside every headline number.

## Reproducibility target

The next implementation stage should add a small standard-library calculation script which reads scenario parameters from CSV and writes a derived scenario table. Facility-level measured values should remain separate from assumptions so that replacing a WUE estimate with a disclosed site value does not require changing the conceptual model.
