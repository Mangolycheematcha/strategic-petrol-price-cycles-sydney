# Cycle Summary

Primary specification: `reconstructed_eod_panel_cap7`.
Detected complete cycles in primary specification: 9.

A complete cycle is defined as `trough_i -> peak_i -> trough_i+1`. Boundary fragments are not promoted to complete cycles.

Formulas:

- `total_duration_days = end_trough_date - start_trough_date`
- `rise_amplitude_cpl = peak_price - start_trough_price`
- `decline_amplitude_cpl = peak_price - end_trough_price`
- `rise_or_recovery_speed_cpl_per_day = rise_amplitude_cpl / rise_duration_days`
- `decline_speed_cpl_per_day = decline_amplitude_cpl / decline_duration_days`

Detection parameters:

| smoothing_window | min_peak_prominence | min_distance_between_peaks | min_cycle_amplitude | min_cycle_duration_days | max_cycle_duration_days | confirmation_window | parameter_set |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 7 | 3.000 | 14 | 8.000 | 10 | 75 | 3 | default_v1 |


Primary cycle metrics:

| cycle_id | start_trough_date | start_trough_price | peak_date | peak_price | end_trough_date | end_trough_price | total_duration_days | rise_duration_days | decline_duration_days | rise_amplitude_cpl | decline_amplitude_cpl | rise_or_recovery_speed_cpl_per_day | decline_speed_cpl_per_day | method | parameter_set | completeness_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| reconstructed_eod_panel_cap7_01 | 2025-04-16 | 165.875 | 2025-04-30 | 194.924 | 2025-05-21 | 158.359 | 35 | 14 | 21 | 29.049 | 36.565 | 2.075 | 1.741 | reconstructed_eod_panel_cap7 | default_v1 | complete |
| reconstructed_eod_panel_cap7_02 | 2025-05-21 | 158.359 | 2025-06-10 | 193.083 | 2025-06-22 | 172.701 | 32 | 20 | 12 | 34.724 | 20.382 | 1.736 | 1.698 | reconstructed_eod_panel_cap7 | default_v1 | complete |
| reconstructed_eod_panel_cap7_03 | 2025-06-22 | 172.701 | 2025-07-08 | 200.813 | 2025-07-27 | 160.594 | 35 | 16 | 19 | 28.112 | 40.219 | 1.757 | 2.117 | reconstructed_eod_panel_cap7 | default_v1 | complete |
| reconstructed_eod_panel_cap7_04 | 2025-07-27 | 160.594 | 2025-08-06 | 190.594 | 2025-08-28 | 165.888 | 32 | 10 | 22 | 30.000 | 24.707 | 3.000 | 1.123 | reconstructed_eod_panel_cap7 | default_v1 | complete |
| reconstructed_eod_panel_cap7_05 | 2025-08-28 | 165.888 | 2025-09-10 | 196.013 | 2025-10-03 | 166.386 | 36 | 13 | 23 | 30.126 | 29.627 | 2.317 | 1.288 | reconstructed_eod_panel_cap7 | default_v1 | complete |
| reconstructed_eod_panel_cap7_06 | 2025-10-03 | 166.386 | 2025-10-15 | 195.631 | 2025-11-04 | 170.037 | 32 | 12 | 20 | 29.245 | 25.594 | 2.437 | 1.280 | reconstructed_eod_panel_cap7 | default_v1 | complete |
| reconstructed_eod_panel_cap7_07 | 2025-11-04 | 170.037 | 2025-11-18 | 202.004 | 2025-12-03 | 169.037 | 29 | 14 | 15 | 31.968 | 32.968 | 2.283 | 2.198 | reconstructed_eod_panel_cap7 | default_v1 | complete |
| reconstructed_eod_panel_cap7_08 | 2025-12-03 | 169.037 | 2025-12-14 | 201.631 | 2026-01-11 | 159.239 | 39 | 11 | 28 | 32.594 | 42.392 | 2.963 | 1.514 | reconstructed_eod_panel_cap7 | default_v1 | complete |
| reconstructed_eod_panel_cap7_09 | 2026-01-11 | 159.239 | 2026-01-26 | 186.704 | 2026-02-17 | 157.723 | 37 | 15 | 22 | 27.465 | 28.982 | 1.831 | 1.317 | reconstructed_eod_panel_cap7 | default_v1 | complete |
