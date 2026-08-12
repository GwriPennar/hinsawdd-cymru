# Project 005 event-study register

## Purpose

This document separates **observed particulate events** from **source attribution**. It records what the AURN instruments measured, when an external fire incident was reported, and what evidence is still required before connecting the two.

The current event-study window is mid-July 2026 because it contains a broad Welsh particulate episode and the start of the significant Blaenavon wildfire. The separate 11 August smoke-transport episode remains a prospective case study until the official source files contain that reporting day.

## Data-quality check before event attribution

The raw Swansea Roadside file contains a provisional PM2.5 reading of **430 µg/m³ at 01:00 on 14 July 2026**, while the collocated PM10 reading at the same hour is **16.425 µg/m³**. The remaining PM2.5 hours on that day are much lower.

Project 005 therefore retains the raw value but adds a conservative sensitivity flag when all of the following are true:

- the PM2.5 value is provisional;
- PM2.5 is at least 100 µg/m³;
- collocated PM10 is available;
- PM2.5 is more than twice PM10.

In the retained baseline this flags **one observation only**. The screen does not automatically label the value invalid and does not alter the raw file. It produces a parallel `pm25_screened` sensitivity series for event analysis.

This matters because the unscreened Swansea 14 July daily mean is 30.57 µg/m³. Removing only that flagged hour from the sensitivity calculation gives about 12.4 µg/m³ for the remaining valid hours and prevents a single provisional excursion from dominating the event narrative.

## Mid-July observational sequence

### 13–18 July: broad multi-station particulate episode

The network event screen shows the strongest common recent PM2.5 signal on **17–18 July**, before the Blaenavon fire was first reported.

On 18 July the median QC-screened daily PM2.5 value across the seven reference stations was approximately **16.38 µg/m³**, with all seven stations reporting and all seven above their own rolling-year 90th percentile threshold.

This is an important negative-control result: the broad mid-July rise cannot have been caused by the Blaenavon wildfire because it predates the reported start of that incident.

### 19 July: Blaenavon fire begins

South Wales Fire and Rescue Service was reported as receiving the initial Blaenavon wildfire call on **Sunday evening, 19 July 2026**. By 21 July the incident covered around **80 hectares** of bracken and gorse and smoke had been significant at times.

The fire-start marker is shown on the Project 005 July chart as timeline context only. It is not used to modify the air-quality measurements or to infer cause.

### 21 July: Newport short particulate pulse

At **22:00 on 21 July**, Newport recorded provisional hourly values of approximately:

- PM2.5: **183.515 µg/m³**;
- PM10: **211.600 µg/m³**;
- NO2: **11.34 µg/m³**.

PM2.5 and PM10 rose together, so this observation is not caught by the internal-consistency QC rule. It is retained as a physically coherent particulate-event candidate.

However, the fire-service statement reported on the evening of 21 July said the current wind direction was expected to carry Blaenavon smoke towards **Nant-y-Glo and Brynmawr**. On that evidence alone, the Newport pulse should **not** be attributed to the Blaenavon fire. Site-specific wind and dispersion evidence is required.

### 22 July: Cardiff particulate episode

Cardiff Centre recorded a separate provisional particulate episode on the morning of 22 July. At 10:00 the collocated readings were approximately:

- PM2.5: **62.0 µg/m³**;
- PM10: **63.77 µg/m³**;
- NO2: **6.27 µg/m³**.

At 11:00 PM2.5 remained about **56 µg/m³** while PM10 was about **61.84 µg/m³**. This coherent fine-particulate rise, with PM2.5 close to PM10, is a useful transported-aerosol candidate. It still cannot be assigned to wildfire without meteorological and satellite support.

## Recent-period site-relative result

To distinguish common regional variation from station-specific excess, Project 005 now calculates for each station-day:

`site PM2.5 - median PM2.5 at the other reporting AURN sites`

At least four peer stations are required. This is an observational residual, **not source apportionment**.

For the latest 70-day window versus the preceding 70 days:

- **Swansea Roadside**: mean site-relative PM2.5 increases from about **+1.66 to +3.78 µg/m³**, a change of **+2.13 µg/m³**. Its correlation with the other-station median remains high at about 0.88, while its PM2.5–NO2 correlation rises from about 0.52 to 0.72.
- **Port Talbot Margam**: mean site-relative PM2.5 increases from about **+0.55 to +3.27 µg/m³**, a change of **+2.73 µg/m³**. Its correlation with the other-station median rises from about 0.87 to 0.92, while its PM2.5–NO2 correlation remains around 0.46.

The cautious interpretation is that both sites share substantial regional variability but also show a larger local/site-relative excess in the recent period. Swansea's stronger recent PM2.5–NO2 relationship is **compatible with** a larger local combustion/traffic contribution, but it does not identify a source. Port Talbot's pattern is different and remains compatible with several local or industrial explanations.

## Fire timeline sources

- ITV Cymru Wales, 21 July 2026, *Firefighters tackling 'significant' wildfire in Blaenavon*: reports the initial Sunday-evening call, approximately 80 hectares affected, significant smoke, and the fire-service wind-direction warning towards Nant-y-Glo and Brynmawr.
  - `https://www.itv.com/news/wales/2026-07-21/firefighters-tackling-significant-wildfire-in-blaenavon`
- Welsh Government, 23 July 2026, wildfire update: records Blaenavon as one of two significant ongoing Welsh fires and describes the multi-agency response.
  - `https://media.service.gov.wales/news/update-from-the-cabinet-minister-for-local-government-housing-and-planning-sian-gwenllian-on-wildfires-across-wales`

## Meteorological evidence available for the next stage

Air Quality in Wales lists **modelled wind speed and modelled wind direction** for Swansea Roadside and both **measured and modelled wind speed/direction** for Port Talbot Margam. Its Openair documentation explains that the modelled weather is WRF-based, updated daily, and uses a roughly 10 km × 10 km grid intended to represent regional synoptic conditions rather than local site airflow.

This is the preferred next meteorological layer because it can be paired directly with the air-quality monitoring sites. It should be supplemented, where useful, by Met Office weather observations/analysis rather than replaced by a consumer weather feed.

## Satellite layer

NASA Earthdata Worldview and FIRMS are reserved for independent spatial evidence of active fires and visible smoke/hotspots. Satellite observations can establish that smoke existed and where a plume appeared to travel, but they are not a substitute for the ground-level PM2.5 measurements.

## Evidence ladder for an attribution claim

A wildfire-attribution statement should only be considered when several independent layers agree:

1. a credible ground-level PM2.5 event survives QC sensitivity checks;
2. fire timing overlaps the event;
3. wind/dispersion conditions support transport from fire to monitor;
4. satellite/fire products support the spatial plume path where available;
5. alternative explanations such as traffic, industry, dust or wider regional aerosol are considered.

Until those conditions are met, Project 005 uses language such as **event candidate**, **coincident**, **compatible with**, or **not supported by the available wind evidence**, rather than claiming causation.
