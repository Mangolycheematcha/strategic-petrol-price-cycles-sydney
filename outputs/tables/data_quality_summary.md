# Data Quality Summary

Cleaning and audit checks are parameterised and counted before output generation.

| metric | value | notes |
| --- | --- | --- |
| raw_rows | 994353 | All loaded buffer and analysis rows. |
| missing_explicit_station_id_rows | 994353 | Historical files reviewed here do not expose an official station id field; station_id is derived from station name, address, suburb, postcode and brand. |
| missing_derived_station_id_rows | 0 | Rows without enough station text to derive a stable station identifier. |
| invalid_timestamp_rows | 6 | Dropped before daily aggregation. |
| missing_price_rows | 0 | Dropped before daily aggregation. |
| missing_postcode_rows | 0 | Dropped before geographic filtering. |
| non_u91_rows | 775289 | Filtered out; only U91-compatible labels are retained. |
| outside_configured_postcode_rows | 102727 | Configured operational Sydney range is 2000-2234; this is not a strict metropolitan boundary. |
| impossible_or_extreme_price_rows | 0 | Filtered using parameterised range [50.0, 350.0] cents per litre. |
| exact_duplicate_events | 3 | Dropped after reporting so exact repeated records do not double-count update events. |
| clean_buffer_and_analysis_events | 116328 | Rows available after cleaning and filtering. |
| clean_analysis_events | 108923 | Rows inside final analysis period only. |
| analysis_start | 2025-04-01 | Inclusive final analysis period start. |
| analysis_end | 2026-03-31 | Inclusive final analysis period end. |
| unique_analysis_stations | 683 | Denominator used for station coverage rates. |
