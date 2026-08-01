# Wales calendar-year warming stripes

This is an additional visualization for Project 001, following the warming-stripes model created by Professor Ed Hawkins at the University of Reading.

## What each stripe means

Each vertical stripe represents one **calendar year** in the official Met Office Wales annual mean-temperature series, from 1884 through the latest complete published calendar year.

The colour represents that year's temperature relative to the Wales average for **1961–2010**:

- blue: cooler than the 1961–2010 average;
- red: warmer than the 1961–2010 average.

The visualization intentionally removes axes and detailed labels in its pure form so that the long-term change can be understood immediately. A labelled version is also generated with the date range, interpretation, data source and attribution.

## Important distinction from the main analysis

The warming stripes use **complete calendar years and official annual values only**. They do not include the provisional July 2026 scenario and do not answer the project's narrower August-to-July ranking question.

The two views are complementary:

- `analysis.py` asks whether August 2025 to July 2026 is the warmest equivalent August-to-July period;
- `warming_stripes.py` shows the long-term calendar-year temperature pattern for Wales.

## Reproduce

From the repository root, after running the main analysis:

```bash
python projects/001-rolling-temperature/analysis.py
python projects/001-rolling-temperature/warming_stripes.py
```

Generated outputs:

- `figures/wales_calendar_year_warming_stripes.png`
- `figures/wales_calendar_year_warming_stripes.svg`
- `figures/wales_calendar_year_warming_stripes_labelled.png`
- `figures/wales_calendar_year_warming_stripes_labelled.svg`
- `data/derived/wales_calendar_year_warming_stripes.csv`

The derived CSV records the official annual value, reference mean and anomaly used for every stripe.

## Attribution and licence

Warming-stripes design: **Professor Ed Hawkins, National Centre for Atmospheric Science, University of Reading**.

The University of Reading's Wales warming-stripes graphics are licensed under **CC BY 4.0**, which permits sharing and adaptation with attribution. This repository's reproduction explicitly credits the original design and uses the official UK Met Office Wales annual temperature series.

References:

- [University of Reading: Climate stripes](https://www.reading.ac.uk/planet/climate-resources/climate-stripes)
- [Show Your Stripes: Wales](https://showyourstripes.info/l/europe/unitedkingdom/wales/)
