# Research protocol v0.1

## Purpose and epistemic status

This is a prospective protocol for new calculations, written after reading relevant claims and some literature. It is **not** a preregistration made before exposure to the evidence. The initiator has expressed scepticism of solar-dominant attribution. The safeguards below are intended to make that prior position less influential, not to claim perfect neutrality.

Freeze the experiment specification in Git before numerical execution. Record amendments and their reasons; label post-hoc exploration explicitly. No outcome is required for project success. Evidence is weighted by relevance, measurement quality, assumptions and reproducibility, not by an equal quota of papers on each side.

## Separate hypotheses

H1: Solar variability affects some aspects of climate. H2: a robust solar approximately 1,000-year or 2,400–2,500-year component is recoverable. H3: it has stable phase and amplitude sufficient for prediction. H4: its climatic effect dominates modern global warming. H5: a particular transport mechanism explains observations more successfully than alternatives. H6: a particular cycle supports a dated cooling or glacier forecast.

Acceptance of H1 does not accept H2–H6. Rejection of one fixed-period model does not reject all solar variability. Modern attribution concerns the causes of change, not the fact that most energy entering the climate system originates from the Sun.

## Workstream A: claim and source audit

Obtain original public post permalinks and dates; currently quotations and figures are supplied by the initiator, not independently authenticated. Preserve exact claim text and distinguish the advocate's assertion from the book's. Do not publish insults or speculate about motives.

Acquire lawful access to the book, recording edition, ISBN, chapter, page and figure. Trace each material figure to original datasets, processing and citations. Do not redistribute the book or screenshots without checking rights. Check corrections, later replications and disagreements. Sources sharing archives, authors or model assumptions are not independent votes.

Use inclusion criteria fixed in advance: a source must bear on a registered claim, method or required observation. Prefer original papers, author-supplied methods and official dataset documentation. Reviews and assessments supply synthesis; an author's commentary establishes what the author argues, not that the argument is correct. Record abstract-only and inaccessible sources rather than silently promoting them to full-method review.

## Workstream B: acquire and freeze data

Use [datasets.json](datasets.json) as the acquisition queue, not evidence of downloads already completed. Record permanent product identifier, version, direct file URL, retrieval timestamp, licence, SHA-256, units, spatial coverage, temporal coverage, missing-value rules and processing history. Keep immutable raw snapshots where terms permit; otherwise retain a manifest and retrieval instructions.

Start with global temperature and both observation-based and reconstructed solar irradiance products. Do not label a model-derived solar CDR a continuous instrumental measurement back to 1610. Evaluate more than one independently constructed solar composite where available; document shared instruments and calibration disagreements. Use spectral irradiance for UV hypotheses rather than assuming TSI is a complete measure of solar influence.

For paleoclimate retain archive resolution, seasonality and age-model ensembles. Distinguish radiocarbon age from calendar age. Explicitly define BP=1950 and astronomical year numbering; never silently introduce or remove year zero. Do not treat IntCal calibration values as solar forcing or temperature. Reproduce the cited IntCal13-based method before assessing newer products as sensitivity analyses.

## Workstream C: reproduce and test periodicity

Recover raw or published derived inputs for the original figures before attempting exact replication. Record all selected periods, band widths, filter order, detrending, boundary treatment, normalization, amplitudes, phases and extrapolation dates. Where these are unavailable, label any reconstruction an approximation, not the original graph.

Compare the published reconstruction families, including solar-supportive results and geomagnetically corrected alternatives. Test signal detection separately from source attribution. Use Fourier/multitaper and wavelet methods appropriate to sampling and chronology; evaluate edge effects, wavelet cones of influence and finite record length. A few millennial cycles do not permit precise phase forecasts by default.

Use several realistic nulls: autocorrelated noise, nonstationary/stochastic alternatives where justified, and synthetic series generated from the archive/sampling model. Apply the *entire* period/phase/filter search to each surrogate. Correct for multiple comparisons across periods, lags, archives and processing choices. Include injected-signal recovery and false-positive calibration; a non-detection is not proof of absence without adequate power.

For grand minima use event start/end and dating uncertainty, not only midpoints. Preserve clustering and nonuniform detectability in null simulations. The quoted 54% highlighted coverage is not a p-value. Test fixed published windows against new or genuinely excluded events, and account for any phase/threshold fitting.

## Workstream D: modern climate attribution

First build descriptive annual temperature and TSI diagnostics in their original units, with raw series and clearly labelled smoothing. Lock the common complete-year period in the data manifest. Show start-date and solar-cycle endpoint sensitivity, including the incomplete 1978 year. Do not use a simple correlation, chosen dual-axis scaling or a significant time trend as a causal attribution result.

Then compare physically constrained alternatives: solar forcing only; natural forcings including volcanism; anthropogenic forcings; and combined forcings. Account for greenhouse gases, aerosols, land-use effects, relevant internal variability and ocean heat uptake. Avoid treating time-correlated predictors as independent causal evidence. Use a transparent energy-balance benchmark before more flexible statistical models.

Pre-specify or train-select lags and response times; test thermal inertia and initial-condition sensitivity rather than assuming that flat present forcing implies zero response. Include uncertainty in forcing, temperature and feedbacks. Keep equilibrium climate sensitivity, transient response and empirical regression coefficients distinct.

Use blocked time validation, training-only preprocessing and nested selection for flexible models. Globally familiar historical periods are retrospective holdouts, not genuinely unseen evidence. Freeze any future forecast with a timestamp, score it without retuning and report failed predictions as well as successes. Comparison metrics include prediction errors, interval coverage and physical consistency, not just in-sample R².

## Workstream E: indirect mechanisms and broader book themes

Build an explicit causal diagram for solar UV/ozone/circulation/meridional transport/radiative loss/heat storage. Specify measurable intermediate quantities, sign, lag, magnitude and uncertainty for each link. Test against circulation changes caused by greenhouse forcing or internal variability. A change in absorbed sunlight caused by terrestrial albedo or clouds is not automatically a change in the Sun's emitted energy.

Use the strongest author formulation of Winter Gatekeeper, including its acknowledgement of human influence. Require an energy-budget calculation, not dismissal based only on TSI. Compare CERES-era energy fluxes, ocean heat content and atmosphere/reanalysis products while accounting for shared inputs and observational limitations.

Treat orbital cycles, abrupt glacial events, tides, volcanism, historical climate and greenhouse gases as separate thematic audits after page-level access. Findings on glacial or regional timescales cannot be transferred to modern global attribution without a demonstrated mechanism. Glaciers require a separate response model; do not turn a solar scenario into a universal melt timetable.

## Workstream F: communication and review

Before publication, an independent reviewer should check the strongest favourable evidence, all key quotations and the numerical reproduction. Review may change the conclusion. Record disagreements in a decision log and maintain a correction history. Do not claim the project itself is peer-reviewed unless an identifiable review has occurred.

Every chart must name dataset versions, units, coverage, baseline, analysis date and uncertainty. Use Python-generated dark-mode-first figures with readable alternatives. Distinguish measurements, proxy reconstructions, fitted models and projections visually and verbally. No generative scientific graphics. No publication of a visually persuasive curve before validation of what it represents.

## Completion gates

Stage A: source register, claim ledger, limitations, protocol and structural tests. Stage B: acquired/checksummed datasets and replicated descriptive diagnostics. Stage C: sensitivity-tested spectral and attribution comparisons, including negative results. Stage D: independently reviewed report and public summary.

Current work reaches Stage A only. No new quantitative climate result, forecast or final whole-book verdict should be represented as complete.
