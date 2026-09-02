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

## Published conclusion (September 2026 refresh)

Using the published July 2026 Met Office value of **17.8°C**:

- August 2025 to July 2026 mean: **10.61°C**;
- previous August-to-July high: **10.32°C**, in 2006-07;
- margin over previous high: **+0.29°C**;
- rank among August-to-July periods: **1st of 142**;
- rank among all monthly-start 12-month windows: **5th**.

July 2026 is present in the retained official monthly series. Earlier workflow versions used an illustrative 18.0°C scenario only while the month was absent from the published table.

## Verification run, 1 September 2026

The project was rerun end to end against an exact-byte download of the public Met Office Wales series.

| Item | Verified value |
|---|---|
| Source last updated | `01-Sep-2026 11:56` |
| Exact source SHA-256 | `1d31f8913bdf127550f42e5f8e97cd39270f4bc9c2f6251528d91068340543f0` |
| Published monthly coverage | January 1884 to August 2026 |
| Complete years reconciled | 142 |
| Maximum absolute difference from official annual column | **0.02192°C** |
| Primary and independent period mean agreement | **Pass** |
| Primary and independent historical rank agreement | **Pass** |
| Primary and independent break-even July agreement | **Pass** |
| Automated tests | **43 passed** |

The two implementations produced the same practical result:

- published July 2026 input: **10.6098630137°C**;
- rank among August-to-July periods: **1st**;
- previous high: **10.3150684932°C**, August 2006 to July 2007;
- July value required to exceed it: **14.3290322581°C**.

The independent implementation uses Python's standard library and `Decimal`. It imports none of the pandas analysis functions. Differences at the last floating-point digits are below `3 × 10⁻¹⁴°C` and arise only from binary floating-point representation.

## Earlier verification run, 1 August 2026

An earlier snapshot (source last updated `01-Jul-2026 11:33`, coverage through June 2026) used an illustrative July scenario pending publication. That provisional workflow is superseded by the September 2026 refresh above.

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

The exact upstream snapshot and its manifest are retained in the repository. The validation workflow runs on every pull request and push, downloads the current upstream file again, reruns both implementations and retains the evidence as a workflow artifact.
