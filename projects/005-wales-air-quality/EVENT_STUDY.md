# Project 005 event-study register

## Purpose

This document separates **observed particulate events** from **source attribution**. It records what the AURN instruments measured, when external fire incidents were reported, and what independent evidence is still required before connecting the two.

Two event windows are now retained:

- mid-July 2026, which provides useful positive and negative controls around the start of the significant Blaenavon wildfire;
- the **11 August 2026 overnight particulate episode**, which is now present in the official AURN annual files and is analysed at hourly physical-clock resolution because Swansea daily coverage is incomplete.

## Data-quality check before event attribution

The raw Swansea Roadside file contains a provisional PM2.5 reading of **430 µg/m³ at 01:00 on 14 July 2026**, while the collocated PM10 reading at the same hour is **16.425 µg/m³**. The remaining PM2.5 hours on that day are much lower.

Project 005 therefore retains the raw value but adds a conservative sensitivity flag when all of the following are true:

- the PM2.5 value is provisional;
- PM2.5 is at least 100 µg/m³;
- collocated PM10 is available;
- PM2.5 is more than twice PM10.

In the retained baseline this flags **one observation only**. The screen does not automatically label the value invalid and does not alter the raw file. It produces a parallel `pm25_screened` sensitivity series for event analysis.

The unscreened Swansea 14 July daily mean is 30.57 µg/m³. Removing only that flagged hour from the sensitivity calculation leaves roughly **12.4 µg/m³** across the remaining valid hours and prevents a single provisional excursion from dominating the event narrative.

## Mid-July observational sequence

### 13–18 July: broad multi-station particulate episode

The network event screen shows the strongest common recent PM2.5 signal on **17–18 July**, before the Blaenavon fire was first reported.

On 18 July the median QC-screened daily PM2.5 value across the seven reference stations was approximately **16.38 µg/m³**, with all seven stations reporting and all seven above their own rolling-year 90th-percentile threshold.

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

## 11 August 2026 overnight event

The latest official source snapshot now includes **11 August 2026**.

The daily baseline continues to enforce the 18-hour completeness rule. Swansea Roadside has only five observations assigned to the 11 August AURN reporting day and therefore has **no published Project 005 daily mean** for that date.

For event analysis, however, AURN's `10 August 24:00` record is physically midnight at the start of 11 August. Combining that physical-clock observation with the five subsequent reporting-day records gives six real Swansea measurements from **00:00 to 05:00 GMT**:

| GMT hour ending | PM2.5 | PM10 | NO2 |
|---|---:|---:|---:|
| 00:00 | 51 | 48.31 | 10.52 |
| 01:00 | 10 | 16.43 | 7.65 |
| 02:00 | 27 | 35.75 | 8.03 |
| 03:00 | 27 | 29.95 | 7.08 |
| 04:00 | 47 | 44.45 | 10.71 |
| 05:00 | 48 | 52.18 | 10.14 |

Across those six physical-clock hours:

- mean PM2.5: **35.0 µg/m³**;
- maximum PM2.5: **51.0 µg/m³** at midnight GMT;
- Swansea's preceding-365-day hourly PM2.5 95th percentile: **20.0 µg/m³**;
- **5 of 6 hours** were at or above that station-specific 95th-percentile threshold;
- mean PM10: **37.84 µg/m³**;
- mean NO2: **9.02 µg/m³**;
- mean PM2.5/PM10 ratio: approximately **0.88**.

The simultaneous PM2.5 and PM10 rise, combined with relatively modest NO2 in the observed hours, is **compatible with a fine-particle aerosol episode and is not well described as a simple traffic-only spike**. That is still not a wildfire attribution.

Coverage at Swansea stops after 05:00, so the event cannot be summarised as a valid full-day Swansea mean.

### Same-day spatial context

The physical-clock 11 August summary shows a west/south-west-heavy pattern in this seven-site network:

- **Swansea Roadside:** 6 valid hours, mean PM2.5 **35.0**, 5 hours at/above its prior-year hourly p95;
- **Port Talbot Margam:** 24 hours, mean **13.96**, 6 hours at/above its p95 of 17;
- **Narberth:** 24 hours, mean **10.02**, 4 hours at/above its p95 of 13.73;
- **Cardiff Centre:** 21 hours, mean **7.19**, no hours at/above its p95;
- **Newport:** 24 hours, mean **5.73**, none at/above its p95;
- **Wrexham:** 24 hours, mean **5.63**, none at/above its p95;
- **Chepstow A48:** 20 hours, mean **5.55**, none at/above its p95.

This spatial pattern is useful evidence for the next attribution stage. It is **compatible with transported aerosol affecting western/south-western sites more strongly**, but wind and satellite evidence are required before relating it to the Blaenavon fire or any other source.

The dedicated chart `wales_aurn_pm25_aug11_smoke_window_dark` plots the physical-clock hourly observations and makes Swansea's later missing coverage explicit.

## Recent-period site-relative result

To distinguish common regional variation from station-specific excess, Project 005 calculates for each station-day:

`site PM2.5 - median PM2.5 at the other reporting AURN sites`

At least four peer stations are required. This is an observational residual, **not source apportionment**.

For the latest 70-day window, **3 June–11 August 2026**, versus the preceding 70 days:

- **Swansea Roadside:** QC-screened mean rises from **8.91 to 10.03 µg/m³ (+12.6%)**. Its mean site-relative PM2.5 increases from **+1.68 to +3.79 µg/m³**, a change of **+2.11 µg/m³**. Correlation with the other-station median remains about 0.88, while PM2.5–NO2 correlation rises from about 0.51 to 0.71.
- **Port Talbot Margam:** mean rises from **7.91 to 9.99 µg/m³ (+26.3%)**. Its site-relative mean increases from **+0.54 to +3.35 µg/m³**, a change of **+2.80 µg/m³**. Correlation with the other-station median is about 0.91 in the recent window, while PM2.5–NO2 correlation remains about 0.46.

The cautious interpretation is that both sites share substantial regional variability but also show a larger local/site-relative excess in the recent period. Swansea's stronger recent PM2.5–NO2 relationship is compatible with a larger local combustion/traffic contribution to its longer-window mean, but it does not identify a source. Port Talbot's pattern is different and remains compatible with several local or industrial explanations.

The QC sensitivity is visible rather than hidden: Swansea's recent raw-period change would be **+15.7%** if the single provisional 430 µg/m³ excursion were left in the daily average, compared with **+12.6%** in the screened sensitivity series.

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
