<img width="2172" height="724" alt="image" src="https://github.com/user-attachments/assets/cda5a4df-bc91-4062-b326-0605a204f811" />



📄 [Read the full report](Report/strategic_petrol_price_cycles_sydney_report.pdf)

🖼️ [View raw-data demo figure](figures/sydney_u91_daily_average_mar2026.png)

## Overview

This repository presents an applied economics and market data analytics project examining strategic petrol price cycles in Sydney’s retail fuel market. The project began as an undergraduate economics research report and was later revised into a portfolio-style research project with updated ACCC market monitoring evidence, literature review, methodology framing and market-surveillance discussion.

The project studies Sydney petrol price cycles as a transparent consumer-market case. It connects retail price-cycle behaviour with Edgeworth cycle theory, ACCC fuel market monitoring, lead-lag detection logic, anomaly-detection framing and the policy tension created by real-time price transparency.

## Research Focus

The project asks:

1. How do Sydney retail petrol price cycles behave across the observed period?
2. To what extent do the observed cycles align with Edgeworth price-cycle theory?
3. How can lead-lag behaviour, failed restorations and false starts be interpreted as market-surveillance indicators?
4. How does real-time price transparency affect both consumer search and retailer monitoring capacity?
5. What broader lessons can transparent retail markets offer for market surveillance and digital market infrastructure?

## Project Contribution

This project does not claim to prove illegal collusion or explicit price fixing. Instead, it interprets Sydney petrol price cycles as patterns consistent with strategic interdependence and cyclical pricing behaviour in a transparent oligopolistic market.

The contribution is threefold:

* It applies industrial organisation theory to a real-world Australian consumer market.
* It extends the original report with ACCC evidence from 2023–2026 and a stronger literature review.
* It reframes petrol price cycles as a market-surveillance case involving transparency, lead-lag behaviour and anomaly detection.

## Repository Structure

```text
Report/          Final revised report in PDF and editable Word format
data/raw/        Raw FuelCheck input notes, source manifest, and the retained March 2026 CSV
data/processed/  Reproducible processed daily price series
docs/            Research decisions and limitations for the reproducible analysis
figures/         Legacy March 2026 demo figure
notebooks/       Reproducible notebooks for the raw-data demo and cycle analysis
outputs/figures/ Generated analysis figures
outputs/tables/  Generated audit, robustness, and cycle result tables
src/             Reusable data loading, cleaning, aggregation, detection, and output code
tests/           Pytest coverage for daily-price methods and cycle detection
```

## Methods

The reproducible extension uses official NSW FuelCheck price-history files from Data.NSW for 2025-04-01 to 2026-03-31, with March 2025 used only as a buffer for finite end-of-day reconstruction. The official source is the Data.NSW FuelCheck dataset and CKAN resource list:

* https://data.nsw.gov.au/data/dataset/fuel-check
* https://data.nsw.gov.au/data/api/3/action/package_show?id=a97a46fc-2bdd-4b90-ac7f-0cb1e8d7ac3b

The workflow treats the FuelCheck history as price update events rather than complete daily market snapshots. It standardises station fields, U91 fuel labels, timestamps in Australia/Sydney time, price values, and the existing operational Sydney postcode range of 2000-2234. That postcode range is retained for comparability with the March 2026 demo, but it is not a strict metropolitan administrative boundary.

Daily Sydney U91 prices are constructed using five alternatives:

* `update_event_mean`: mean of all price update events each day; retained as the legacy-style comparator because frequently updated stations receive more weight.
* `station_day_last_mean`: last update per station-day, then equal-weight mean across active stations.
* `station_day_mean_equal_weight`: mean within each station-day, then equal-weight mean across active stations.
* `station_day_median`: last update per station-day, then cross-station median.
* `reconstructed_eod_panel_cap7`: finite end-of-day panel using last known station price with a 7-day staleness cap.

The selected primary specification is `reconstructed_eod_panel_cap7`. It gives stations equal weight, reduces direct update-frequency bias, and includes stations without same-day updates only when a recent known price is available. The selection remains assumption-dependent, so the other methods are retained as robustness specifications.

Complete price cycles are detected algorithmically, not by manually selecting dates. A complete cycle is defined as `trough_i -> peak_i -> trough_i+1`. The default detector uses a 7-day smoothing window, minimum peak prominence of 3 cents per litre, minimum peak distance of 14 days, minimum cycle amplitude of 8 cents per litre, and plausible complete-cycle duration bounds of 10-75 days. Detected turning-point dates and prices are confirmed against the nearby unsmoothed daily series.

## Key Concepts

* Edgeworth price cycles
* strategic pricing behaviour
* price restoration
* lead-lag behaviour
* anomaly detection
* market transparency
* ACCC fuel monitoring
* digitally transparent market infrastructure
* market surveillance

## Limitations

This project is a research portfolio project, not a full econometric paper. It does not claim to establish explicit collusion, illegal price fixing, market manipulation, or causal effects.

Important limitations:

* FuelCheck historical records may be price update events rather than complete daily market snapshots.
* `update_event_mean` can repeatedly weight stations that update prices more often.
* Active station-day methods omit stations that did not update on a given day.
* The reconstructed end-of-day series depends on forward-fill and staleness-cap assumptions.
* The postcode 2000-2234 filter is an operational Sydney approximation, not a precise boundary.
* Cycle detection results can change with data coverage and parameter choices.

## Raw Data Demonstration

The original March 2026 notebook is retained as a small reproducibility demonstration:

* `notebooks/01_fuelcheck_raw_data_demo.ipynb`
* `data/raw/price_history_checks_mar2026.csv`
* `data/processed/sydney_u91_daily_average_mar2026.csv`
* `figures/sydney_u91_daily_average_mar2026.png`

The broader 12-month analysis is implemented in reusable Python modules and a separate notebook rather than adding all logic to the demo notebook.

<img width="3600" height="1800" alt="image" src="https://github.com/user-attachments/assets/a81019ba-e133-4e84-a268-3bee7eeab63e" />

## How to Reproduce

Install dependencies:

```bash
pip install -r requirements.txt
```

Run tests:

```bash
pytest
```

Run the full analysis from the repository root:

```bash
python -m src.run_analysis
```

The script downloads official monthly FuelCheck resources to the ignored local cache `data/raw/fuelcheck_history/`, writes `data/raw/source_manifest.csv`, and regenerates processed outputs.

Run notebooks from a clean kernel:

* `notebooks/01_fuelcheck_raw_data_demo.ipynb`
* `notebooks/02_cycle_analysis.ipynb`

## Project Outputs

Key generated outputs:

* `data/processed/daily_price_methods.csv`: unified daily price series for all aggregation methods.
* `data/raw/source_manifest.csv`: official source URL, access date, covered period, file size and SHA-256 checksum for each raw monthly file used locally.
* `outputs/tables/data_quality_summary.csv` and `.md`: cleaning and audit counts.
* `outputs/tables/robustness_comparison.csv` and `.md`: method comparison and selected primary specification.
* `outputs/tables/cycle_metrics.csv`: complete peak-trough cycle metrics.
* `outputs/tables/cycle_summary.md`: cycle definitions, formulas and primary results.
* `outputs/figures/`: daily series with turning points, method comparison, station coverage, and cycle amplitude-duration figures.
* `docs/research_decisions.md`: data, aggregation, cycle-detection and limitation decisions.

## Status

Current version: portfolio research report plus reproducible exploratory Sydney U91 FuelCheck price-cycle analysis.



