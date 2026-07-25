from __future__ import annotations

import pandas as pd

from src.config import AnalysisConfig
from src.construct_daily_prices import (
    reconstructed_eod_panel,
    station_day_last_mean,
    station_day_mean_equal_weight,
    update_event_mean,
)
from src.load_and_clean import parse_fuelcheck_timestamp


def test_timestamp_parser_handles_iso_and_day_first_formats() -> None:
    parsed = parse_fuelcheck_timestamp(pd.Series(["2026-03-12 00:05:26", "12/03/2026 0:05"]))
    assert parsed.iloc[0].date().isoformat() == "2026-03-12"
    assert parsed.iloc[1].date().isoformat() == "2026-03-12"


def test_update_event_mean_weights_each_update_event() -> None:
    config = AnalysisConfig(analysis_start="2025-04-01", analysis_end="2025-04-01", buffer_start="2025-04-01")
    events = pd.DataFrame(
        {
            "station_id": ["a", "a", "b"],
            "date": [pd.Timestamp("2025-04-01").date()] * 3,
            "timestamp": pd.to_datetime(["2025-04-01 09:00", "2025-04-01 17:00", "2025-04-01 12:00"]),
            "price_cpl": [100.0, 100.0, 200.0],
        }
    )
    result = update_event_mean(events, config)
    assert result.loc[0, "daily_price"] == 400.0 / 3.0
    assert result.loc[0, "n_update_events"] == 3


def test_station_day_last_selects_last_record_per_station_day() -> None:
    config = AnalysisConfig(analysis_start="2025-04-01", analysis_end="2025-04-01", buffer_start="2025-04-01")
    events = pd.DataFrame(
        {
            "station_id": ["a", "a", "b"],
            "date": [pd.Timestamp("2025-04-01").date()] * 3,
            "timestamp": pd.to_datetime(["2025-04-01 09:00", "2025-04-01 17:00", "2025-04-01 12:00"]),
            "price_cpl": [100.0, 120.0, 200.0],
        }
    )
    result = station_day_last_mean(events, config)
    assert result.loc[0, "daily_price"] == 160.0
    assert result.loc[0, "n_stations"] == 2


def test_equal_weight_removes_direct_update_count_weighting() -> None:
    config = AnalysisConfig(analysis_start="2025-04-01", analysis_end="2025-04-01", buffer_start="2025-04-01")
    events = pd.DataFrame(
        {
            "station_id": ["a", "a", "a", "b"],
            "date": [pd.Timestamp("2025-04-01").date()] * 4,
            "timestamp": pd.to_datetime(
                ["2025-04-01 09:00", "2025-04-01 10:00", "2025-04-01 11:00", "2025-04-01 12:00"]
            ),
            "price_cpl": [100.0, 100.0, 100.0, 200.0],
        }
    )
    event_result = update_event_mean(events, config)
    equal_result = station_day_mean_equal_weight(events, config)
    assert event_result.loc[0, "daily_price"] == 125.0
    assert equal_result.loc[0, "daily_price"] == 150.0


def test_reconstructed_eod_forward_fill_respects_staleness_cap() -> None:
    config = AnalysisConfig(analysis_start="2025-04-01", analysis_end="2025-04-05", buffer_start="2025-03-31")
    events = pd.DataFrame(
        {
            "station_id": ["a", "b"],
            "date": [pd.Timestamp("2025-04-01").date(), pd.Timestamp("2025-04-01").date()],
            "timestamp": pd.to_datetime(["2025-04-01 09:00", "2025-04-01 10:00"]),
            "price_cpl": [100.0, 200.0],
        }
    )
    daily, stale = reconstructed_eod_panel(events, config, staleness_cap_days=2)
    by_date = daily.set_index("date")
    assert by_date.loc[pd.Timestamp("2025-04-03").date(), "n_stations"] == 2
    assert by_date.loc[pd.Timestamp("2025-04-04").date(), "n_stations"] == 0
    assert stale.loc[stale["date"] == pd.Timestamp("2025-04-03").date(), "max_staleness_days"].iloc[0] == 2
