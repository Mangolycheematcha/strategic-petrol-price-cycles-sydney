## Strategic Price Cycles in Sydney’s Retail Petrol Market


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

This project does not claim to prove illegal collusion or explicit price fixing. Instead, it interprets Sydney petrol price cycles as evidence of strategic interdependence and cyclical pricing behaviour in a transparent oligopolistic market.

The contribution is threefold:

* It applies industrial organisation theory to a real-world Australian consumer market.
* It extends the original report with ACCC evidence from 2023–2026 and a stronger literature review.
* It reframes petrol price cycles as a market-surveillance case involving transparency, lead-lag behaviour and anomaly detection.

## Repository Structure

```text
report/      Final revised report in PDF and editable Word format
figures/     Figures used in the report, including original analysis and ACCC evidence
notes/       Literature review notes, methodology framework and future-work plan
data/        Data-source notes and reproducibility plan
```

## Methods

The project uses a descriptive and theory-driven empirical framework. It does not implement full algorithmic cycle detection or econometric modelling. Instead, it adopts a structured market-analysis approach based on:

* visual and descriptive cycle assessment
* cycle duration and amplitude interpretation
* relenting and discounting phase analysis
* lead-lag detection logic
* failed-cycle and false-start interpretation
* ACCC market monitoring evidence
* wholesale-retail price context
* transparency-effect discussion

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

This project is a research portfolio project, not a full econometric paper. It does not claim to establish explicit collusion or illegal price fixing. It also does not yet implement full raw-data processing using NSW FuelCheck station-level data.

A future technical extension could include:

* downloading full NSW FuelCheck station-level data
* cleaning daily station-level price observations
* constructing brand-level daily average prices
* applying algorithmic cycle detection
* estimating lead-lag relationships by brand and station
* identifying failed restorations and anomalous price movements
* building a reproducible Python workflow

## Raw Data Demonstration

This repository includes a small reproducibility demonstration using NSW FuelCheck monthly price history data. The current demo processes March 2026 FuelCheck data, filters for Sydney metro U91 observations, constructs a daily average petrol price series, exports a processed CSV file, and generates a reproducible visualisation.

This demonstration is designed as a proof of workflow rather than a full econometric price-cycle detection exercise. It shows how publicly available station-level fuel price data can be transformed into an analytical time-series output suitable for further market-cycle analysis.

The March 2026 sample captures an upward price-restoration phase in Sydney U91 petrol prices, followed by a short high-price plateau. It should not be interpreted as a complete petrol price cycle because the sample does not cover a full trough-to-peak-to-trough sequence. A longer multi-month dataset would be required for formal cycle detection, lead-lag analysis, failed-restoration identification, and anomaly scoring.

Outputs from this demonstration include:

a cleaned daily average Sydney U91 price dataset;
a reproducible Python notebook;
a March 2026 daily average price figure;
a foundation for future FuelCheck-based cycle detection work.

<img width="3600" height="1800" alt="image" src="https://github.com/user-attachments/assets/a81019ba-e133-4e84-a268-3bee7eeab63e" /># 

## How to Reproduce the Raw-Data Demo

1. Download the March 2026 NSW FuelCheck price history CSV.
2. Save it under `data/raw/price_history_checks_mar2026.csv`.
3. Open `notebooks/01_fuelcheck_raw_data_demo.ipynb`.
4. Run all cells.
5. The notebook will generate:
   - `data/processed/sydney_u91_daily_average_mar2026.csv`
   - `figures/sydney_u91_daily_average_mar2026.png`

## Project Outputs

- Full revised research report
- All-figures overview image
- FuelCheck March 2026 raw-data demonstration notebook
- Processed Sydney U91 daily average dataset
- Raw-data demo figure
- Methodology and reproducibility roadmap

## Status

Current version: polished portfolio research report.

Future version: optional reproducible data analytics extension.
