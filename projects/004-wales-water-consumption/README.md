# Project 004 — Water consumption in Wales

## Research question

How much water is used in Wales, how is public-supply water divided between households and non-households, and how material is direct operational water use by Welsh data centres today and under plausible future growth?

This is an independent public research project. It is not a political publication and does not advocate for or against data-centre development. Its purpose is to quantify the available evidence, expose uncertainty and keep measured values separate from modelled estimates.

## Headline findings

### Wales-wide public supply

Welsh Government reports that Dŵr Cymru Welsh Water and Hafren Dyfrdwy supplied around **920 megalitres per day (Ml/d)** in 2024–25 to meet demand in Wales. Private water supplies were estimated at **13.8 Ml/d**.

Source: https://www.gov.wales/wellbeing-wales-2025-resilient-wales-html

`1 Ml = 1 million litres`, so 920 Ml/d is about **920 million litres per day**, or roughly **336 billion litres per year**.

The 920 Ml/d figure is public water supplied, not a measure of every abstraction or every form of water use in Wales.

### Household versus non-household

For public water supplied by water companies, the useful categories are **household** and **non-household**. Non-household includes businesses and industry, but also institutions such as schools, hospitals and other organisations. It should not be relabelled simply as “industry”.

A historical Dŵr Cymru regulatory water-balance breakdown gives household customer consumption of roughly **534 Ml/d** and non-household consumption of roughly **166 Ml/d** for 2021–22, around **76% household / 24% non-household of customer consumption** when those two categories alone are compared.

This split is retained as a working historical estimate only. It is not treated as a current all-Wales census. Dŵr Cymru subsequently restated leakage and per-capita-consumption reporting after an Ofwat investigation, so current APR data should be used wherever possible before publishing a final household/non-household chart.

Sources:
- https://corporate.dwrcymru.com/en/library/annual-performance-reports
- https://www.ofwat.gov.uk/enforcement-case-into-dwr-cymru-welsh-water-welsh-water-about-the-accuracy-of-its-reported-leakage-and-per-capita-consumption-pcc-performance/

### Current drought context

Natural Resources Wales extended **drought status across all of Wales on 30 July 2026** after exceptionally low rainfall, low river flows, declining groundwater and wider environmental impacts. NRW’s drought classification concerns hydrological and environmental conditions; it is not the same thing as a household supply restriction.

Source: https://naturalresources.wales/about-us/news-and-blogs/news/drought-status-extended-across-all-of-wales-as-environment-continues-to-feel-the-strain/?lang=en

## Data centres in Wales

### How many are there?

There is no single universally accepted definition of a data centre and no complete public Welsh census.

The strongest current public synthesis is Senedd Research’s July 2026 briefing. It reports:

- **at least 7 active data-centre sites in South Wales**;
- **1 active data centre in North Wales at St Asaph**;
- several planned sites in both North and South Wales;
- one site may contain multiple data-centre buildings.

This means a raw building count is a poor denominator for water estimation.

Source: https://research.senedd.wales/research-articles/data-centres-in-wales-how-will-wales-manage-a-rapidly-growing-industry/

### Capacity is the better denominator

The UK Department for Science, Innovation and Technology estimated **154 MW of operational colocation data-centre IT capacity in Wales in autumn 2024**. This was the largest regional colocation capacity in Great Britain outside London.

The DSIT figure is not a complete census because it excludes enterprise data centres operated by businesses for their own purposes. It is nevertheless the strongest published national operational-capacity denominator identified for this project.

Source: https://www.gov.uk/government/publications/estimate-of-data-centre-capacity-great-britain-2024/estimate-of-data-centre-capacity-great-britain-2024

## Current direct-water estimate

No authoritative source currently publishes a measured total for direct operational water consumption by all Welsh data centres. Project 004 therefore uses a transparent scenario model rather than presenting an invented measured figure.

The model is:

`direct water use = operational IT capacity × average load factor × 24 hours × WUE`

where WUE is direct site Water Usage Effectiveness in litres per kWh of IT energy.

Using the DSIT **154 MW** operational colocation baseline:

| Scenario | IT load factor | Direct WUE | Estimated water | Share of 920 Ml/d |
|---|---:|---:|---:|---:|
| Low-water | 50% | 0.10 L/kWh | **0.185 Ml/d** | **0.020%** |
| Central | 65% | 0.30 L/kWh | **0.721 Ml/d** | **0.078%** |
| High-water | 80% | 0.90 L/kWh | **2.661 Ml/d** | **0.289%** |

### Interpretation

The evidence supports a cautious conclusion:

> **Direct operational water use by current Welsh colocation data centres is likely to be well below 1% of Wales-wide public water supply. A reasonable order-of-magnitude central estimate is around 0.7 Ml/d, or about 0.08%, but this is modelled rather than measured.**

The estimate should not be quoted without the word **estimate**.

### Why the range is wide

Water demand is highly sensitive to cooling architecture and weather. Data centres may use dry/free-air cooling, indirect evaporative cooling, chilled-water systems, liquid-to-chip cooling, closed-loop systems or combinations of these technologies.

Vantage’s Cardiff/Newport CWL1 campus, for example, publishes a mixed cooling design including **indirect evaporative air handling units**, **dry-cooler CRAH systems**, pumped DX systems and rack-level liquid-cooling options. It also states that the local climate supports free-air cooling for much of the year.

Source: https://vantage-dc.com/data-center-locations/emea/cardiff-united-kingdom/

Microsoft reports that its fleet-wide WUE fell to **0.27 L/kWh in 2025**, while newer closed-loop designs can eliminate continuing water consumption for cooling after initial fill. These values demonstrate why a single generic “litres per data centre” assumption is unsuitable.

Sources:
- https://blogs.microsoft.com/blog/2026/06/24/inside-microsofts-two-decade-push-to-cut-water-intensity-while-scaling-for-growth/
- https://www.microsoft.com/en-us/microsoft-cloud/blog/2024/12/09/sustainable-by-design-next-generation-datacenters-consume-zero-water-for-cooling/

Academic literature likewise distinguishes direct site water from indirect water associated with electricity generation and manufacturing. Project 004’s headline estimate covers **direct operational site water only**.

Source: https://www.nature.com/articles/s41545-021-00101-w

## Why local impacts can matter even when the national percentage is small

A national percentage can hide local constraints. Senedd Research notes that plans for Vantage’s proposed CWL4 campus at Bridgend state that the water-supply system in the immediate vicinity has **limited capacity to serve the development**, with reinforcement potentially required before occupation.

This means two statements can both be true:

1. present Welsh data-centre water consumption can be a small fraction of national public supply;
2. an individual large development can still be material to a local water-resource zone or distribution network.

Source: https://research.senedd.wales/media/eytgh5cx/data-centres-in-wales.pdf

## Future capacity is a different problem

Current operational water use must not be mixed with planned capacity.

Senedd Research identifies major Welsh developments including approximately:

- **150 MW** at Cardiff East;
- **200 MW** for Microsoft in Newport;
- **around 600 MW** for Vantage CWL4 in Bridgend;
- **349 MW** on Anglesey;
- continued build-out of the Vantage CWL1 campus to **148 MW**.

The UK Government says the **South Wales AI Growth Zone could harness over 1 GW by the early 2030s**.

Sources:
- https://research.senedd.wales/research-articles/data-centres-in-wales-how-will-wales-manage-a-rapidly-growing-industry/
- https://www.gov.uk/government/news/ai-to-power-national-renewal-as-government-announces-billions-of-additional-investment-and-new-plans-to-boost-uk-businesses-jobs-and-innovation

An illustrative 1 GW future operational fleet, if it had the same three load/WUE scenarios, would imply:

| Scenario | Estimated direct water | Share of 920 Ml/d baseline |
|---|---:|---:|
| Low-water | **1.20 Ml/d** | **0.13%** |
| Central | **4.68 Ml/d** | **0.51%** |
| High-water | **17.28 Ml/d** | **1.88%** |

These are **scenario calculations, not forecasts**. Future sites may use substantially lower-water cooling systems, and 920 Ml/d should not be assumed to remain the relevant future Welsh supply baseline.

## What we can say safely

- Wales currently receives about **920 Ml/d** from its two main public water suppliers.
- Household consumption is larger than non-household consumption; the historical Dŵr Cymru customer-consumption split used here is about **76/24**.
- “Non-household” must not be described as synonymous with “industry”.
- Wales has **at least eight active data-centre sites** in the Senedd Research synthesis, but site count is less useful than capacity.
- DSIT’s best published operational colocation estimate is **154 MW**.
- There is **no measured public total** for Welsh data-centre water consumption.
- A transparent first-order model places current direct operational colocation water use at approximately **0.2–2.7 Ml/d**, with a central value near **0.7 Ml/d**.
- That is approximately **0.02–0.29%** of the 2024–25 Wales public-supply figure, with a central estimate near **0.08%**.
- The current national share appears small, but local network/resource-zone effects and future expansion can be much more important.

## Status

**Research baseline v0.1 — 10 August 2026.**

The next stage is facility-level validation: operator, location, operational status, IT MW, cooling system, water source, planning reference and any disclosed annual/peak water demand. Until that is complete, Project 004 deliberately reports a range rather than a false-precision national total.
