from __future__ import annotations

import pandas as pd

from src.detect_cycles import CycleDetectionParams, detect_cycles


def _params() -> CycleDetectionParams:
    return CycleDetectionParams(
        smoothing_window=1,
        min_peak_prominence=3.0,
        min_distance_between_peaks=2,
        min_cycle_amplitude=5.0,
        min_cycle_duration_days=2,
        max_cycle_duration_days=10,
        confirmation_window=0,
        parameter_set="test",
    )


def test_cycle_detector_identifies_known_peak_trough_sequence() -> None:
    dates = pd.date_range("2025-01-01", periods=11, freq="D")
    prices = [105, 100, 110, 120, 115, 102, 108, 125, 111, 98, 104]
    daily = pd.DataFrame(
        {
            "date": dates.date,
            "daily_price": prices,
            "n_stations": 2,
            "n_update_events": 2,
            "coverage_rate": 1.0,
            "method": "test_method",
        }
    )
    cycles, turns = detect_cycles(daily, "test_method", _params())
    assert len(cycles) == 2
    assert list(turns["turning_type"]).count("peak") >= 2
    assert list(turns["turning_type"]).count("trough") >= 3


def test_incomplete_boundary_segments_are_not_complete_cycles() -> None:
    dates = pd.date_range("2025-01-01", periods=7, freq="D")
    prices = [100, 110, 120, 115, 102, 108, 125]
    daily = pd.DataFrame(
        {
            "date": dates.date,
            "daily_price": prices,
            "n_stations": 2,
            "n_update_events": 2,
            "coverage_rate": 1.0,
            "method": "test_method",
        }
    )
    cycles, _ = detect_cycles(daily, "test_method", _params())
    assert cycles.empty


def test_cycle_metric_formulas_are_correct() -> None:
    dates = pd.date_range("2025-01-01", periods=7, freq="D")
    prices = [105, 100, 112, 120, 110, 102, 109]
    daily = pd.DataFrame(
        {
            "date": dates.date,
            "daily_price": prices,
            "n_stations": 2,
            "n_update_events": 2,
            "coverage_rate": 1.0,
            "method": "test_method",
        }
    )
    cycles, _ = detect_cycles(daily, "test_method", _params())
    cycle = cycles.iloc[0]
    assert cycle["total_duration_days"] == 4
    assert cycle["rise_duration_days"] == 2
    assert cycle["decline_duration_days"] == 2
    assert cycle["rise_amplitude_cpl"] == 20
    assert cycle["decline_amplitude_cpl"] == 18
    assert cycle["rise_or_recovery_speed_cpl_per_day"] == 10
    assert cycle["decline_speed_cpl_per_day"] == 9
