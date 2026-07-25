# Research Decisions

## Scope

The analysis period is 2025-04-01 to 2026-03-31. A buffer beginning 2025-03-01 is used only to initialise finite end-of-day reconstruction; buffer days are excluded from final daily series, cycle metrics and robustness tables.

## Geographic Definition

The operational Sydney filter remains postcode 2000-2234 to keep continuity with the earlier March 2026 demonstration. This range is not a strict Sydney metropolitan administrative boundary and should not be described as one.

## Daily Price Specification

The primary specification is `reconstructed_eod_panel_cap7`. It is selected because it equal-weights stations, reduces update-frequency weighting, and includes stations without a same-day update only when a recent known price is available within a finite 7-day staleness cap. This does not prove it is uniquely best; the active-station methods and median specification are retained as robustness specifications because the reconstructed series depends on forward-fill assumptions.

The update-event mean remains a comparator, not the preferred market-level measure, because it can repeatedly weight stations that update prices more often.

## Robustness Results

| method | date_range | number_of_daily_observations | mean_daily_price | standard_deviation | min_price | max_price | average_station_coverage | average_update_events_per_day | detected_cycle_count | median_cycle_duration | median_amplitude | correlation_with_proposed_baseline | mean_absolute_deviation_from_baseline | main_bias_or_risk | selected | selection_rationale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| reconstructed_eod_panel_cap7 | 2025-04-01 to 2026-03-31 | 365 | 182.210 | 19.242 | 157.723 | 258.070 | 0.720 | 298.419 | 9 | 35.000 | 30.000 | 1.000 | 0.000 | Equal-weights stations with finite forward-fill, but depends on the chosen staleness cap and may carry stale prices. | True | Selected as the primary specification because it gives stations equal weight, reduces update-frequency bias, and retains stations with no same-day update only when a recent known price is available under the finite staleness cap. |
| station_day_last_mean | 2025-04-01 to 2026-03-31 | 365 | 181.591 | 19.021 | 155.729 | 258.117 | 0.299 | 298.419 | 9 | 35.000 | 31.031 | 0.983 | 2.459 | Equal-weights stations with same-day updates but omits stations with no update that day. | False | Retained as a robustness specification for active station-days using end-of-day updates only. |
| station_day_mean_equal_weight | 2025-04-01 to 2026-03-31 | 365 | 181.803 | 18.941 | 155.451 | 258.030 | 0.299 | 298.419 | 9 | 35.000 | 31.111 | 0.982 | 2.535 | Equal-weights active station-days but uses within-day mean prices rather than end-of-day market prices. | False | Retained as a robustness specification that removes direct update-count weighting within each station-day. |
| station_day_median | 2025-04-01 to 2026-03-31 | 365 | 180.247 | 21.219 | 153.450 | 259.900 | 0.299 | 298.419 | 9 | 31.000 | 39.000 | 0.951 | 4.726 | Robust to high or low station outliers, but still only covers stations with same-day updates and uses each station-day's last price. | False | Retained as a robustness specification that reduces sensitivity to cross-station price outliers. |
| update_event_mean | 2025-04-01 to 2026-03-31 | 365 | 181.017 | 18.982 | 155.784 | 257.870 | 0.299 | 298.419 | 9 | 35.000 | 30.908 | 0.978 | 2.751 | Weights stations by update-event frequency, so frequently updated stations can influence the daily mean more than quieter stations. | False | Retained as the legacy-style comparator because it directly averages update events. |


## End-of-Day Staleness Sensitivity

| staleness_cap_days | mean_daily_price | mean_coverage_rate | mean_valid_stations | mean_staleness_days | max_staleness_days | daily_observations |
| --- | --- | --- | --- | --- | --- | --- |
| 3.000 | 182.251 | 0.586 | 400.323 | 0.896 | 3.000 | 365.000 |
| 7.000 | 182.210 | 0.720 | 492.077 | 1.704 | 7.000 | 365.000 |
| 14.000 | 181.902 | 0.790 | 539.340 | 2.408 | 14.000 | 365.000 |


## Cycle Detection Parameters

The initial parameter set is recorded as `default_v1` and was chosen before inspecting cycle-level results: a 7-day rolling mean for turning-point detection, minimum peak prominence of 3.0 cents per litre, minimum distance of 14 days between peaks, minimum cycle amplitude of 8.0 cents per litre, and plausible complete-cycle duration bounds of 10-75 days. Turning-point dates and prices are confirmed against the nearby unsmoothed daily series within +/- 3 days.

No post-hoc parameter tuning was applied in this workflow. Cycles close to the minimum amplitude, minimum prominence, or duration thresholds should be treated as parameter-sensitive.

| smoothing_window | min_peak_prominence | min_distance_between_peaks | min_cycle_amplitude | min_cycle_duration_days | max_cycle_duration_days | confirmation_window | parameter_set |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 7 | 3.000 | 14 | 8.000 | 10 | 75 | 3 | default_v1 |


## Limitations

FuelCheck historical files appear to record price update events rather than complete daily market snapshots. Methods based only on same-day update events can miss stations that continued operating without updating. The reconstructed end-of-day panel reduces that omission but relies on forward-fill and staleness-cap assumptions. Cycle detection is exploratory and descriptive; it is not causal identification, collusion detection, or evidence of illegal market conduct.
