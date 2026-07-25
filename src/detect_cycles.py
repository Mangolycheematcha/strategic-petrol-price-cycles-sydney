from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd
from scipy.signal import find_peaks

from .config import DEFAULT_CONFIG, AnalysisConfig


@dataclass(frozen=True)
class CycleDetectionParams:
    smoothing_window: int
    min_peak_prominence: float
    min_distance_between_peaks: int
    min_cycle_amplitude: float
    min_cycle_duration_days: int
    max_cycle_duration_days: int
    confirmation_window: int
    parameter_set: str

    @classmethod
    def from_config(cls, config: AnalysisConfig = DEFAULT_CONFIG) -> "CycleDetectionParams":
        return cls(
            smoothing_window=config.smoothing_window,
            min_peak_prominence=config.min_peak_prominence,
            min_distance_between_peaks=config.min_distance_between_peaks,
            min_cycle_amplitude=config.min_cycle_amplitude,
            min_cycle_duration_days=config.min_cycle_duration_days,
            max_cycle_duration_days=config.max_cycle_duration_days,
            confirmation_window=config.turning_point_confirmation_window,
            parameter_set=config.parameter_set_name,
        )


def _smoothed_prices(series: pd.Series, window: int) -> pd.Series:
    if window <= 1:
        return series.astype(float)
    return series.astype(float).rolling(window=window, center=True, min_periods=1).mean()


def _confirm_turning_point(df: pd.DataFrame, index: int, kind: str, window: int) -> int:
    start = max(index - window, 0)
    end = min(index + window + 1, len(df))
    subset = df.iloc[start:end]
    if kind == "peak":
        return int(subset["daily_price"].idxmax())
    return int(subset["daily_price"].idxmin())


def detect_turning_points(
    daily_prices: pd.DataFrame,
    params: CycleDetectionParams | None = None,
) -> pd.DataFrame:
    params = params or CycleDetectionParams.from_config()
    df = daily_prices.sort_values("date").reset_index(drop=True).copy()
    df["date"] = pd.to_datetime(df["date"])
    df["smooth_price"] = _smoothed_prices(df["daily_price"], params.smoothing_window)

    peak_idx, _ = find_peaks(
        df["smooth_price"].to_numpy(),
        prominence=params.min_peak_prominence,
        distance=params.min_distance_between_peaks,
    )
    trough_idx, _ = find_peaks(
        -df["smooth_price"].to_numpy(),
        prominence=params.min_peak_prominence,
        distance=params.min_distance_between_peaks,
    )

    rows = []
    seen: set[tuple[str, pd.Timestamp]] = set()
    for kind, indices in [("trough", trough_idx), ("peak", peak_idx)]:
        for raw_index in indices:
            confirmed_index = _confirm_turning_point(df, int(raw_index), kind, params.confirmation_window)
            key = (kind, df.loc[confirmed_index, "date"])
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "turning_type": kind,
                    "date": df.loc[confirmed_index, "date"],
                    "price": float(df.loc[confirmed_index, "daily_price"]),
                    "smooth_detection_date": df.loc[int(raw_index), "date"],
                    "smooth_detection_price": float(df.loc[int(raw_index), "smooth_price"]),
                    "parameter_set": params.parameter_set,
                }
            )
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


def detect_cycles(
    daily_prices: pd.DataFrame,
    method: str,
    params: CycleDetectionParams | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    params = params or CycleDetectionParams.from_config()
    turning_points = detect_turning_points(daily_prices, params)
    troughs = turning_points.loc[turning_points["turning_type"] == "trough"].copy()
    peaks = turning_points.loc[turning_points["turning_type"] == "peak"].copy()
    rows = []

    troughs = troughs.sort_values("date").reset_index(drop=True)
    peaks = peaks.sort_values("date").reset_index(drop=True)
    for i in range(len(troughs) - 1):
        start = troughs.loc[i]
        end = troughs.loc[i + 1]
        between = peaks.loc[(peaks["date"] > start["date"]) & (peaks["date"] < end["date"])]
        if between.empty:
            continue
        peak = between.loc[between["price"].idxmax()]

        total_duration = (end["date"] - start["date"]).days
        rise_duration = (peak["date"] - start["date"]).days
        decline_duration = (end["date"] - peak["date"]).days
        rise_amplitude = float(peak["price"] - start["price"])
        decline_amplitude = float(peak["price"] - end["price"])
        if not (params.min_cycle_duration_days <= total_duration <= params.max_cycle_duration_days):
            continue
        if rise_duration <= 0 or decline_duration <= 0:
            continue
        if rise_amplitude < params.min_cycle_amplitude or decline_amplitude < params.min_cycle_amplitude:
            continue

        rows.append(
            {
                "cycle_id": f"{method}_{len(rows) + 1:02d}",
                "start_trough_date": start["date"].date().isoformat(),
                "start_trough_price": float(start["price"]),
                "peak_date": peak["date"].date().isoformat(),
                "peak_price": float(peak["price"]),
                "end_trough_date": end["date"].date().isoformat(),
                "end_trough_price": float(end["price"]),
                "total_duration_days": int(total_duration),
                "rise_duration_days": int(rise_duration),
                "decline_duration_days": int(decline_duration),
                "rise_amplitude_cpl": rise_amplitude,
                "decline_amplitude_cpl": decline_amplitude,
                "rise_or_recovery_speed_cpl_per_day": rise_amplitude / rise_duration,
                "decline_speed_cpl_per_day": decline_amplitude / decline_duration,
                "method": method,
                "parameter_set": params.parameter_set,
                "completeness_flag": "complete",
            }
        )
    cycles = pd.DataFrame(rows)
    return cycles, turning_points


def detect_cycles_for_methods(
    daily_methods: pd.DataFrame,
    params: CycleDetectionParams | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    params = params or CycleDetectionParams.from_config()
    cycle_frames = []
    turning_frames = []
    for method, group in daily_methods.groupby("method"):
        cycles, turning = detect_cycles(group, method=method, params=params)
        if not cycles.empty:
            cycle_frames.append(cycles)
        if not turning.empty:
            turning = turning.copy()
            turning["method"] = method
            turning_frames.append(turning)
    cycles_all = pd.concat(cycle_frames, ignore_index=True) if cycle_frames else pd.DataFrame()
    turning_all = pd.concat(turning_frames, ignore_index=True) if turning_frames else pd.DataFrame()
    params_df = pd.DataFrame([asdict(params)])
    return cycles_all, turning_all, params_df
