# Hinsawdd Cymru visual publication standard

## Default presentation

Dark mode is the default publication style for all new Hinsawdd Cymru charts and graphics.

The canonical dark palette is:

- figure background: `#080c16`
- plot-panel background: `#0f172a`
- primary text: `#f8fafc`
- secondary text: `#94a3b8`
- grid and borders: `#334155`
- primary cyan: `#22d3ee`
- primary blue: `#60a5fa`
- wetter or positive rainfall marks: `#38bdf8`
- drier or negative rainfall marks: `#f59e0b`
- strong dry highlight: `#fb7185`

Colour must always be supported by labels, a zero/reference line, direct annotation or another non-colour cue where interpretation depends on it.

## Required formats

Every newly published chart should normally produce:

- a 1600 × 900 widescreen PNG;
- a 1600 × 900 widescreen SVG;
- a 1080 × 1080 square PNG;
- a 1080 × 1080 square SVG.

The widescreen chart is the primary report and web format. The square chart is the primary social format. Both must contain the essential title, units, time window, reference period and source information rather than relying on surrounding text.

## Light variants

Light-background variants are optional compatibility outputs, not the default. They should be generated only when a publication, print workflow or accessibility requirement specifically needs them. A light version must use the same data, labels and scientific interpretation as its dark counterpart.

Existing historical light charts remain valid provenance outputs and should not be deleted merely to enforce the new default.

## Scientific annotation

Every chart must state, as applicable:

- geography;
- measured variable and unit;
- calendar or rolling-period definition;
- observational coverage;
- reference period, normally 1991–2020;
- source organisation and dataset;
- source update date;
- whether a line is observed, smoothed, fitted or projected.

Statistical continuations must be visibly distinguished from observations and labelled as illustrative unless they are based on an identified physical climate-projection framework. Descriptive trend extrapolation must never be presented as an official Met Office, UKCP or IPCC forecast.

## Reproducibility

Charts must be generated reproducibly from repository code and retained source provenance. Matplotlib is the chart-rendering layer; Seaborn may set general typography and styling. Generative-image tools must not be used to manufacture scientific plots or data marks.

Tests should verify at least:

- expected output files;
- exact raster dimensions;
- dark-background identity for canonical outputs;
- units and reference labels;
- agreement between displayed headline values and derived data.

## Accessibility and editorial restraint

Use a clear hierarchy, restrained grids and direct labels. Avoid ornamental effects that compete with the evidence. Do not rely on red–green contrast alone. Keep footnotes readable in both output shapes and make the first frame understandable without interaction.
