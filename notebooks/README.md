# Notebooks

This folder contains reproducible notebooks for the FuelCheck workflows.

## Notebooks

`01_fuelcheck_raw_data_demo.ipynb`

This notebook processes March 2026 NSW FuelCheck data, filters for Sydney metro U91 observations, constructs a daily average petrol price series and exports both a processed CSV and a figure.

This is a proof-of-workflow demonstration, not a full econometric price-cycle detection model.

`02_cycle_analysis.ipynb`

This notebook calls the reusable `src` pipeline for the 2025-04-01 to 2026-03-31 Sydney U91 exploratory cycle analysis, then displays data-quality checks, robustness results, cycle metrics and generated figures.
