# Project 004 source register

Accessed 10 August 2026 unless otherwise stated.

This register records the evidence used by Project 004 and the role each source plays. Preference is given to government, regulator, parliamentary research, operator technical disclosures and peer-reviewed research. Commercial directories are not used as the primary basis for national totals.

## Welsh water supply, consumption and drought

### Welsh Government — Wellbeing of Wales 2025: A resilient Wales

URL: https://www.gov.wales/wellbeing-wales-2025-resilient-wales-html

Supports:
- approximately **920 Ml/day** supplied in 2024–25 by Dŵr Cymru Welsh Water and Hafren Dyfrdwy to meet demand in Wales;
- approximately **13.8 Ml/day** supplied through private water supplies.

Use in Project 004: present-day Wales public-supply comparison baseline.

Caveat: this is not total abstraction or total consumptive water use in Wales.

### Natural Resources Wales — drought status extended across all Wales

URL: https://naturalresources.wales/about-us/news-and-blogs/news/drought-status-extended-across-all-of-wales-as-environment-continues-to-feel-the-strain/?lang=en

Supports:
- drought status extended across all Wales on **30 July 2026**;
- hydrological/environmental context including low rainfall, river flows and groundwater stress.

Use in Project 004: current context only. NRW drought status is not treated as synonymous with household restrictions.

### Dŵr Cymru Welsh Water — Annual Performance Reports

URL: https://corporate.dwrcymru.com/en/library/annual-performance-reports

Supports:
- regulatory water-balance and performance reporting;
- historical household, non-household, leakage and consumption components.

Use in Project 004: source family for reconciling household/non-household water consumption and leakage.

Caveat: the current README retains an older working 2021–22 customer-consumption split and labels it historical pending a fully reconciled current-year extraction.

### Ofwat — enforcement case on Dŵr Cymru leakage and per-capita consumption reporting

URL: https://www.ofwat.gov.uk/enforcement-case-into-dwr-cymru-welsh-water-welsh-water-about-the-accuracy-of-its-reported-leakage-and-per-capita-consumption-pcc-performance/

Supports:
- regulatory finding that Dŵr Cymru misreported leakage and per-capita consumption performance in 2020–21 and 2021–22;
- reason for treating historical company water-balance values cautiously when constructing a present-day series.

Use in Project 004: provenance and quality-control caveat.

## Welsh data-centre population and capacity

### Department for Science, Innovation and Technology — Estimate of Data Centre Capacity: Great Britain 2024

URL: https://www.gov.uk/government/publications/estimate-of-data-centre-capacity-great-britain-2024/estimate-of-data-centre-capacity-great-britain-2024

Supports:
- estimated **154 MW operational colocation maximum rated IT load in Wales** in autumn 2024;
- Wales as the largest regional colocation market outside London in this dataset;
- explicit exclusion of enterprise/private data centres from the estimate.

Use in Project 004: principal denominator for the current direct-water scenario model.

### Senedd Research — Data centres in Wales: how will Wales manage a rapidly growing industry?

HTML: https://research.senedd.wales/research-articles/data-centres-in-wales-how-will-wales-manage-a-rapidly-growing-industry/

PDF: https://research.senedd.wales/media/eytgh5cx/data-centres-in-wales.pdf

Published 31 July 2026.

Supports:
- no universally accepted definition of a data centre;
- **at least seven active sites in South Wales** and **one active site in St Asaph, North Wales**;
- distinction between sites and multiple buildings within a campus;
- existing and proposed Welsh data-centre geography;
- proposed/under-development capacities including Cardiff, Newport, Bridgend and Anglesey;
- published discussion of data-centre direct and indirect water demand;
- Vantage CWL4 planning evidence that the immediate water-supply system has limited capacity to serve the planned development and may require reinforcement.

Use in Project 004: principal Welsh site-count synthesis, planning/growth evidence and local-water-constraint evidence.

### UK Government — South Wales AI Growth Zone

URL: https://www.gov.uk/government/news/ai-to-power-national-renewal-as-government-announces-billions-of-additional-investment-and-new-plans-to-boost-uk-businesses-jobs-and-innovation

Supports:
- statement that the South Wales AI Growth Zone could harness **over 1 GW** by the early 2030s.

Use in Project 004: basis for a deliberately illustrative 1,000 MW future sensitivity scenario.

Caveat: the Project 004 1 GW calculation is not a forecast of delivered capacity, occupancy or water demand.

## Operator cooling and water-efficiency evidence

### Vantage Data Centers — CWL1 Cardiff campus

URL: https://vantage-dc.com/data-center-locations/emea/cardiff-united-kingdom/

Supports:
- CWL1 full-campus critical IT capacity of approximately **148 MW**;
- mixed cooling architecture including indirect evaporative air handling, dry-cooler CRAH systems/pumped DX and rack-level liquid-cooling options.

Use in Project 004: evidence that Welsh hyperscale cooling cannot be represented by one fixed generic WUE.

### Microsoft — fleet water intensity

URL: https://blogs.microsoft.com/blog/2026/06/24/inside-microsofts-two-decade-push-to-cut-water-intensity-while-scaling-for-growth/

Supports:
- Microsoft fleet-wide WUE reported at approximately **0.27 L/kWh in 2025**;
- material reductions in water intensity as cooling systems changed.

Use in Project 004: contemporary benchmark showing that large modern operators can operate at relatively low direct WUE.

### Microsoft — next-generation zero-water cooling design

URL: https://www.microsoft.com/en-us/microsoft-cloud/blog/2024/12/09/sustainable-by-design-next-generation-datacenters-consume-zero-water-for-cooling/

Supports:
- closed-loop liquid-cooling architecture designed to avoid continuing fresh-water consumption for cooling after initial system fill.

Use in Project 004: lower-bound technology context, not a claim that all Welsh Microsoft facilities use this design.

## Academic evidence

### Mytton, D. — Data centre water consumption, npj Clean Water (2021)

URL: https://www.nature.com/articles/s41545-021-00101-w

Supports:
- distinction between direct on-site water and indirect water associated with electricity;
- WUE as a standard direct site-water metric;
- large variation in data-centre water consumption by cooling and operating conditions;
- transparency limitations in publicly available data-centre water reporting.

Use in Project 004: conceptual and methodological boundary for the direct-water model.

## Evidence still required

The following are intentionally unresolved rather than estimated without evidence:

- a complete site-by-site census of private/enterprise Welsh data centres;
- measured annual water consumption for each operational Welsh data-centre campus;
- exact water source for each site: potable, non-potable, reclaimed or direct abstraction;
- peak-day and drought-mode water consumption by site;
- current-year all-Wales household/non-household customer consumption reconciled across both Welsh public suppliers;
- facility-level WUE for the existing 154 MW Welsh colocation fleet.

These gaps are part of the published result: national direct data-centre water use is currently a scenario estimate, not a measured national statistic.
