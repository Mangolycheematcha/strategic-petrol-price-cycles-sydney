from __future__ import annotations

import pandas as pd

from .config import DEFAULT_CONFIG, AnalysisConfig


REQUIRED_DAILY_COLUMNS = [
    "date",
    "daily_price",
    "n_stations",
    "n_update_events",
    "coverage_rate",
    "method",
]


def _analysis_slice(clean_events: pd.DataFrame, config: AnalysisConfig) -> pd.DataFrame:
    start = pd.Timestamp(config.analysis_start).date()
    end = pd.Timestamp(config.analysis_end).date()
    return clean_events.loc[clean_events["date"].between(start, end)].copy()


def _event_counts(analysis: pd.DataFrame) -> pd.DataFrame:
    return (
        analysis.groupby("date", as_index=False)
        .agg(n_update_events=("price_cpl", "size"))
    )


def _coverage(series: pd.DataFrame, total_stations: int, method: str) -> pd.DataFrame:
    out = series.copy()
    out["coverage_rate"] = out["n_stations"] / max(total_stations, 1)
    out["method"] = method
    return out[REQUIRED_DAILY_COLUMNS]


def update_event_mean(clean_events: pd.DataFrame, config: AnalysisConfig = DEFAULT_CONFIG) -> pd.DataFrame:
    analysis = _analysis_slice(clean_events, config)
    total_stations = analysis["station_id"].nunique()
    daily = (
        analysis.groupby("date", as_index=False)
        .agg(
            daily_price=("price_cpl", "mean"),
            n_stations=("station_id", "nunique"),
            n_update_events=("price_cpl", "size"),
        )
    )
    return _coverage(daily, total_stations, "update_event_mean")


def station_day_last_mean(clean_events: pd.DataFrame, config: AnalysisConfig = DEFAULT_CONFIG) -> pd.DataFrame:
    analysis = _analysis_slice(clean_events, config)
    total_stations = analysis["station_id"].nunique()
    last = (
        analysis.sort_values(["station_id", "date", "timestamp"])
        .groupby(["station_id", "date"], as_index=False)
        .tail(1)
    )
    daily = (
        last.groupby("date", as_index=False)
        .agg(daily_price=("price_cpl", "mean"), n_stations=("station_id", "nunique"))
        .merge(_event_counts(analysis), on="date", how="left")
    )
    return _coverage(daily, total_stations, "station_day_last_mean")


def station_day_mean_equal_weight(clean_events: pd.DataFrame, config: AnalysisConfig = DEFAULT_CONFIG) -> pd.DataFrame:
    analysis = _analysis_slice(clean_events, config)
    total_stations = analysis["station_id"].nunique()
    station_day = (
        analysis.groupby(["station_id", "date"], as_index=False)
        .agg(station_price=("price_cpl", "mean"))
    )
    daily = (
        station_day.groupby("date", as_index=False)
        .agg(daily_price=("station_price", "mean"), n_stations=("station_id", "nunique"))
        .merge(_event_counts(analysis), on="date", how="left")
    )
    return _coverage(daily, total_stations, "station_day_mean_equal_weight")


def station_day_median(clean_events: pd.DataFrame, config: AnalysisConfig = DEFAULT_CONFIG) -> pd.DataFrame:
    """Median across stations using each station-day's last observed update as its representative price."""
    analysis = _analysis_slice(clean_events, config)
    total_stations = analysis["station_id"].nunique()
    last = (
        analysis.sort_values(["station_id", "date", "timestamp"])
        .groupby(["station_id", "date"], as_index=False)
        .tail(1)
    )
    daily = (
        last.groupby("date", as_index=False)
        .agg(daily_price=("price_cpl", "median"), n_stations=("station_id", "nunique"))
        .merge(_event_counts(analysis), on="date", how="left")
    )
    return _coverage(daily, total_stations, "station_day_median")


def reconstructed_eod_panel(
    clean_events: pd.DataFrame,
    config: AnalysisConfig = DEFAULT_CONFIG,
    staleness_cap_days: int | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    cap = staleness_cap_days if staleness_cap_days is not None else config.eod_staleness_cap_days
    analysis = _analysis_slice(clean_events, config)
    total_stations = analysis["station_id"].nunique()
    start = pd.Timestamp(config.buffer_start).date()
    analysis_start = pd.Timestamp(config.analysis_start).date()
    end = pd.Timestamp(config.analysis_end).date()
    date_index = pd.date_range(start, end, freq="D").date

    last_events = (
        clean_events.loc[clean_events["date"].between(start, end)]
        .sort_values(["station_id", "date", "timestamp"])
        .groupby(["station_id", "date"], as_index=False)
        .tail(1)
    )
    if last_events.empty:
        empty = pd.DataFrame(columns=REQUIRED_DAILY_COLUMNS)
        stale = pd.DataFrame(columns=["date", "staleness_cap_days", "mean_staleness_days", "median_staleness_days", "max_staleness_days"])
        return empty, stale

    price_panel = (
        last_events.pivot(index="date", columns="station_id", values="price_cpl")
        .reindex(date_index)
        .ffill()
    )
    update_dates = last_events.assign(update_date=last_events["date"]).pivot(
        index="date", columns="station_id", values="update_date"
    )
    update_dates = update_dates.reindex(date_index).ffill()
    date_frame = pd.DataFrame(
        {station: date_index for station in update_dates.columns},
        index=date_index,
        columns=update_dates.columns,
    )
    staleness = (date_frame - update_dates).apply(lambda col: col.map(lambda value: value.days if pd.notna(value) else pd.NA))
    valid_mask = staleness.le(cap) & price_panel.notna()
    masked_prices = price_panel.where(valid_mask)

    analysis_mask = pd.Series(date_index).between(analysis_start, end).to_numpy()
    analysis_dates = [d for d, keep in zip(date_index, analysis_mask) if keep]
    daily = pd.DataFrame(
        {
            "date": analysis_dates,
            "daily_price": masked_prices.loc[analysis_dates].mean(axis=1).to_numpy(),
            "n_stations": valid_mask.loc[analysis_dates].sum(axis=1).astype(int).to_numpy(),
        }
    )
    daily = daily.merge(_event_counts(analysis), on="date", how="left")
    daily["n_update_events"] = daily["n_update_events"].fillna(0).astype(int)
    daily = _coverage(daily, total_stations, f"reconstructed_eod_panel_cap{cap}")

    stale = pd.DataFrame(
        {
            "date": analysis_dates,
            "staleness_cap_days": cap,
            "mean_staleness_days": staleness.where(valid_mask).loc[analysis_dates].mean(axis=1).to_numpy(),
            "median_staleness_days": staleness.where(valid_mask).loc[analysis_dates].median(axis=1).to_numpy(),
            "max_staleness_days": staleness.where(valid_mask).loc[analysis_dates].max(axis=1).to_numpy(),
            "n_valid_stations": valid_mask.loc[analysis_dates].sum(axis=1).astype(int).to_numpy(),
        }
    )
    return daily, stale


def construct_daily_price_methods(
    clean_events: pd.DataFrame, config: AnalysisConfig = DEFAULT_CONFIG
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    methods = [
        update_event_mean(clean_events, config),
        station_day_last_mean(clean_events, config),
        station_day_mean_equal_weight(clean_events, config),
        station_day_median(clean_events, config),
    ]
    eod_primary, eod_staleness = reconstructed_eod_panel(clean_events, config, config.eod_staleness_cap_days)
    methods.append(eod_primary)

    sensitivity_rows = []
    for cap in config.eod_sensitivity_caps:
        daily, stale = reconstructed_eod_panel(clean_events, config, cap)
        sensitivity_rows.append(
            {
                "staleness_cap_days": cap,
                "mean_daily_price": daily["daily_price"].mean(),
                "mean_coverage_rate": daily["coverage_rate"].mean(),
                "mean_valid_stations": daily["n_stations"].mean(),
                "mean_staleness_days": stale["mean_staleness_days"].mean(),
                "max_staleness_days": stale["max_staleness_days"].max(),
                "daily_observations": len(daily),
            }
        )
    return pd.concat(methods, ignore_index=True), eod_staleness, pd.DataFrame(sensitivity_rows)
