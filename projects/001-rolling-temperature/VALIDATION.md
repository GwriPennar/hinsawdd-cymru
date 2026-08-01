# Validation record

## Purpose

This document records the end-to-end checks applied to Project 001. It distinguishes upstream Met Office validation from checks performed within Hinsawdd Cymru.

## Validation boundary

Hinsawdd Cymru does not independently inspect individual instruments or reproduce the HadUK-Grid interpolation. Those processes are upstream and documented by the Met Office.

The project validates that:

1. the correct official Wales series was captured;
2. its provenance is explicit and tamper-evident;
3. parsing preserves the published monthly values;
4. calendar weighting and rankings are correct;
5. an independent implementation reproduces the headline result;
6. public wording does not overstate provisional or derived values.

## Automated checks

| Check | Acceptance criterion |
|---|---|
| Source identity | Expected Met Office title and complete `year ... ann` header |
| Immutable source | New refresh creates a new snapshot or confirms identical bytes; it never overwrites differing bytes |
| Provenance hash | SHA-256 of the source equals its manifest |
| Monthly continuity | No missing month between the first and latest published month |
| Duplicate protection | No duplicate year-month observations |
| Leap-year handling | Calendar month lengths produce 365 or 366 day periods as appropriate |
| Official annual reconciliation | Annual means reconstructed from rounded monthly values remain within 0.06°C of the official annual column |
| Primary calculation | Current 12-month mean and historical rank are generated from the retained source |
| Independent rerun | Standard-library verifier agrees with the primary result to 1e-12 for shared calculations |
| Scenario labelling | Unpublished July values are labelled illustrative scenarios, not estimates |
| Figure provenance | Graphic states its source, weighting and the exact July input used |
| README consistency | Generated result section is produced from `summary.json` inputs |

## Why annual reconciliation is useful

The official source publishes monthly and annual columns. Reconstructing each complete year from the rounded monthly values tests month ordering, parsing, leap-year weighting and arithmetic against a value produced independently by the upstream dataset.

Small differences are expected because the public monthly values are rounded to 0.1°C and the annual values are published to 0.01°C. A conservative tolerance of 0.06°C is used. This tolerance is a source-reconciliation threshold, not a climatological uncertainty interval.

## Independent rerun

The primary implementation uses pandas. The verifier uses standard-library parsing, `calendar` and `Decimal`, and imports none of the primary calculation functions. The two implementations share only the retained source and the stated research question.

This avoids a common false assurance in which tests simply call the same function that produced the original result.

## Provisional conclusion under test

Using an illustrative July 2026 value of 18.0°C:

- August 2025 to July 2026 mean: approximately 10.63°C;
- previous August-to-July high: approximately 10.32°C, in 2006-07;
- July 2026 value required to exceed it: approximately 14.33°C.

The record ranking is therefore insensitive to the final few hundredths of the July value. The exact mean remains provisional until July is published in the official monthly series.

## Upstream Met Office checks referenced, not reproduced

The Met Office documents:

- station observation quality control;
- comparisons with neighbouring sites;
- site inspections and equipment calibration;
- regression and interpolation across the 1 km grid;
- verification RMSE at withheld or verification stations;
- annual HadUK-Grid releases and provisional monthly updates.

These support confidence in the input product but are outside this repository's reproducible boundary.

## Reproducible Analytical Pipeline principles

The project follows the UK statistical system's RAP principles by using:

- scripted ingestion instead of copy-and-paste;
- version-controlled code and data provenance;
- open-source Python;
- repeatable generated outputs;
- automated tests;
- an independent executable verification path;
- clear separation of official, derived and provisional claims.

## Current status

The validation workflow runs on every pull request and push. Its machine-readable verifier output and exact online source download are retained as workflow artifacts. Once the exact upstream snapshot is committed, this record will include the final source hash, maximum annual reconciliation difference and validation commit.
