# Project 002 plan: Wales temperature pathways

## Research framing

Project 002 asks three linked questions:

1. What does a deliberately simple extrapolation of the observed Wales record produce?
2. What do the newest official climate projections and risk assessments expect?
3. Do sustained observed Wales temperatures remain broadly aligned with the official projection distribution?

The first question is implemented in Stage A. The other questions require official ensemble projection data and are not answered by the linear model.

## Stage A: observed-trend baseline

Status: implemented by `model.py`.

Deliverables:

- modern-period ordinary least-squares baseline;
- full-record OLS sensitivity;
- modern-period Theil-Sen sensitivity;
- moving-block bootstrap trend-fit interval;
- fixed-origin ten-year backtests;
- 2050, 2100 and 2125 milestone values;
- machine-readable outputs and independent verification.

Acceptance rules:

- Project 001 independent verification must pass before fitting;
- only published-input periods may enter the fit;
- the provisional 2025–26 point must be visibly labelled and excluded;
- every future output must state that it is not a physical climate forecast;
- no single regression line may be described as the expected future climate of Wales.

## Stage B: official projection source decision

Candidate source family:

- UKCP18 probabilistic land projections;
- UKCP18 regional or local ensemble products where spatial and temporal resolution are appropriate;
- UK Climate Information products as they become available and documented.

Selection criteria:

- official provenance and stable download route;
- monthly mean-temperature variable;
- sufficient Wales spatial coverage;
- ensemble members or percentiles retained;
- documented baseline and emissions or warming-level assumptions;
- licence compatible with reproducible derived analysis;
- ability to aggregate to a Wales land-area mean;
- ability to reconstruct August-to-July periods.

The source-decision record must explain why one product is appropriate and why alternatives were rejected.

## Stage C: Wales official-projection ensemble

Proposed method:

1. obtain the selected gridded monthly projection product;
2. retain exact source metadata and checksums;
3. identify grid cells intersecting the Wales land boundary;
4. calculate area-weighted monthly Wales means;
5. convert monthly means to calendar-day-weighted August-to-July values;
6. retain the ensemble, scenarios and uncertainty rather than collapsing them to one line;
7. reconcile the historical model period with Project 001 observations using an explicitly documented baseline.

Primary chart:

- observed Project 001 series;
- official ensemble median;
- central 50% and wider 5–95% ranges;
- clearly separated scenarios or global-warming levels.

## Stage D: observed-versus-projected alignment

Tests should focus on sustained climate statistics, not a single record period:

- five-year rolling means;
- ten-year rolling means;
- observed trend slope;
- percentile position within the projection ensemble;
- duration above selected ensemble percentiles;
- sensitivity to baseline and observational revisions.

Possible conclusions:

- broadly aligned;
- currently tracking the warmer part of the ensemble;
- outside the expected range for a sustained period;
- insufficient evidence.

No conclusion that an official projection is outdated should be based solely on the provisional 2025–26 point.

## Stage E: official Welsh evidence context

This is related to the scientific analysis but remains separate from the numerical model. Its purpose is to document the official evidence, assumptions, monitoring arrangements and update cycles used in Wales.

Tasks:

- identify the latest Welsh Government strategies, monitoring frameworks, formal assessments and technical statements;
- review relevant official Senedd proceedings and published committee or plenary records where they clarify scientific evidence, assumptions, responsibilities or update timetables;
- distinguish clearly between scientific evidence, formal government policy and parliamentary scrutiny;
- assess whether official documents specify an update cycle tied to UKCI, CCRA4 or new observations;
- record evidence gaps, ambiguities or inconsistencies without attributing them to a political party;
- prepare neutral research questions requesting current Wales-specific projections, monitoring arrangements and source provenance where these are unclear.

This strand does not assess political parties, manifestos, electoral positions or political performance.

## Update cycle

The model is designed to regenerate whenever Project 001 changes. A later automation may:

1. check whether the official Met Office Wales source includes a new month or revision;
2. refresh and independently verify Project 001;
3. rerun Project 002;
4. open a reviewable pull request rather than silently changing published results.

Automatic direct commits to `main` are not recommended for scientific-result updates.
