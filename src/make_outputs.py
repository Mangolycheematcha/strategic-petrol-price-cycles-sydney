from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from .config import (
    DEFAULT_CONFIG,
    DOCS_DIR,
    OUTPUT_FIGURES_DIR,
    PROCESSED_DIR,
    TABLES_DIR,
    AnalysisConfig,
    ensure_directories,
)


BIAS_RISKS = {
    "update_event_mean": "Weights stations by update-event frequency, so frequently updated stations can influence the daily mean more than quieter stations.",
    "station_day_last_mean": "Equal-weights stations with same-day updates but omits stations with no update that day.",
    "station_day_mean_equal_weight": "Equal-weights active station-days but uses within-day mean prices rather than end-of-day market prices.",
    "station_day_median": "Robust to high or low station outliers, but still only covers stations with same-day updates and uses each station-day's last price.",
}


def method_bias_risk(method: str) -> str:
    if method.startswith("reconstructed_eod_panel"):
        return "Equal-weights stations with finite forward-fill, but depends on the chosen staleness cap and may carry stale prices."
    return BIAS_RISKS.get(method, "Method-specific risk not separately classified.")


def method_rationale(method: str, selected_method: str) -> str:
    if method == selected_method:
        return (
            "Selected as the primary specification because it gives stations equal weight, reduces update-frequency bias, "
            "and retains stations with no same-day update only when a recent known price is available under the finite staleness cap."
        )
    if method == "update_event_mean":
        return "Retained as the legacy-style comparator because it directly averages update events."
    if method == "station_day_last_mean":
        return "Retained as a robustness specification for active station-days using end-of-day updates only."
    if method == "station_day_mean_equal_weight":
        return "Retained as a robustness specification that removes direct update-count weighting within each station-day."
    if method == "station_day_median":
        return "Retained as a robustness specification that reduces sensitivity to cross-station price outliers."
    return "Retained for sensitivity comparison."


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    headers = list(df.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in df.iterrows():
        cells = []
        for value in row:
            if pd.isna(value):
                cells.append("")
            elif isinstance(value, float):
                cells.append(f"{value:.3f}")
            else:
                cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def make_robustness_comparison(
    daily_methods: pd.DataFrame,
    cycles_all: pd.DataFrame,
    config: AnalysisConfig = DEFAULT_CONFIG,
) -> pd.DataFrame:
    baseline = daily_methods.loc[daily_methods["method"] == config.selected_method, ["date", "daily_price"]].rename(
        columns={"daily_price": "baseline_price"}
    )
    rows = []
    for method, group in daily_methods.groupby("method"):
        group = group.sort_values("date")
        merged = group.merge(baseline, on="date", how="inner")
        cycle_subset = cycles_all.loc[cycles_all["method"] == method] if not cycles_all.empty else pd.DataFrame()
        if method == config.selected_method:
            corr = 1.0
            mad = 0.0
        elif len(merged) >= 2:
            corr = merged["daily_price"].corr(merged["baseline_price"])
            mad = (merged["daily_price"] - merged["baseline_price"]).abs().mean()
        else:
            corr = pd.NA
            mad = pd.NA
        rows.append(
            {
                "method": method,
                "date_range": f"{group['date'].min()} to {group['date'].max()}",
                "number_of_daily_observations": int(group["daily_price"].notna().sum()),
                "mean_daily_price": group["daily_price"].mean(),
                "standard_deviation": group["daily_price"].std(),
                "min_price": group["daily_price"].min(),
                "max_price": group["daily_price"].max(),
                "average_station_coverage": group["coverage_rate"].mean(),
                "average_update_events_per_day": group["n_update_events"].mean(),
                "detected_cycle_count": int(len(cycle_subset)),
                "median_cycle_duration": cycle_subset["total_duration_days"].median() if not cycle_subset.empty else pd.NA,
                "median_amplitude": cycle_subset["rise_amplitude_cpl"].median() if not cycle_subset.empty else pd.NA,
                "correlation_with_proposed_baseline": corr,
                "mean_absolute_deviation_from_baseline": mad,
                "main_bias_or_risk": method_bias_risk(method),
                "selected": method == config.selected_method,
                "selection_rationale": method_rationale(method, config.selected_method),
            }
        )
    return pd.DataFrame(rows).sort_values(["selected", "method"], ascending=[False, True])


def write_markdown_table(path: Path, title: str, body: str, df: pd.DataFrame) -> None:
    path.write_text(f"# {title}\n\n{body}\n\n{dataframe_to_markdown(df)}", encoding="utf-8")


def write_cycle_summary(
    cycles_all: pd.DataFrame,
    params_df: pd.DataFrame,
    config: AnalysisConfig = DEFAULT_CONFIG,
) -> None:
    selected = cycles_all.loc[cycles_all["method"] == config.selected_method] if not cycles_all.empty else pd.DataFrame()
    lines = [
        "# Cycle Summary",
        "",
        f"Primary specification: `{config.selected_method}`.",
        f"Detected complete cycles in primary specification: {len(selected)}.",
        "",
        "A complete cycle is defined as `trough_i -> peak_i -> trough_i+1`. Boundary fragments are not promoted to complete cycles.",
        "",
        "Formulas:",
        "",
        "- `total_duration_days = end_trough_date - start_trough_date`",
        "- `rise_amplitude_cpl = peak_price - start_trough_price`",
        "- `decline_amplitude_cpl = peak_price - end_trough_price`",
        "- `rise_or_recovery_speed_cpl_per_day = rise_amplitude_cpl / rise_duration_days`",
        "- `decline_speed_cpl_per_day = decline_amplitude_cpl / decline_duration_days`",
        "",
        "Detection parameters:",
        "",
        dataframe_to_markdown(params_df),
    ]
    if not selected.empty:
        lines.extend(["", "Primary cycle metrics:", "", dataframe_to_markdown(selected)])
    (TABLES_DIR / "cycle_summary.md").write_text("\n".join(lines), encoding="utf-8")


def write_research_decisions(
    robustness: pd.DataFrame,
    eod_sensitivity: pd.DataFrame,
    params_df: pd.DataFrame,
    config: AnalysisConfig = DEFAULT_CONFIG,
) -> None:
    selected_row = robustness.loc[robustness["selected"]].iloc[0]
    text = f"""# Research Decisions

## Scope

The analysis period is {config.analysis_start} to {config.analysis_end}. A buffer beginning {config.buffer_start} is used only to initialise finite end-of-day reconstruction; buffer days are excluded from final daily series, cycle metrics and robustness tables.

## Geographic Definition

The operational Sydney filter remains postcode {config.sydney_postcode_min}-{config.sydney_postcode_max} to keep continuity with the earlier March 2026 demonstration. This range is not a strict Sydney metropolitan administrative boundary and should not be described as one.

## Daily Price Specification

The primary specification is `{config.selected_method}`. It is selected because it equal-weights stations, reduces update-frequency weighting, and includes stations without a same-day update only when a recent known price is available within a finite {config.eod_staleness_cap_days}-day staleness cap. This does not prove it is uniquely best; the active-station methods and median specification are retained as robustness specifications because the reconstructed series depends on forward-fill assumptions.

The update-event mean remains a comparator, not the preferred market-level measure, because it can repeatedly weight stations that update prices more often.

## Robustness Results

{dataframe_to_markdown(robustness)}

## End-of-Day Staleness Sensitivity

{dataframe_to_markdown(eod_sensitivity)}

## Cycle Detection Parameters

The initial parameter set is recorded as `{config.parameter_set_name}` and was chosen before inspecting cycle-level results: a {config.smoothing_window}-day rolling mean for turning-point detection, minimum peak prominence of {config.min_peak_prominence} cents per litre, minimum distance of {config.min_distance_between_peaks} days between peaks, minimum cycle amplitude of {config.min_cycle_amplitude} cents per litre, and plausible complete-cycle duration bounds of {config.min_cycle_duration_days}-{config.max_cycle_duration_days} days. Turning-point dates and prices are confirmed against the nearby unsmoothed daily series within +/- {config.turning_point_confirmation_window} days.

No post-hoc parameter tuning was applied in this workflow. Cycles close to the minimum amplitude, minimum prominence, or duration thresholds should be treated as parameter-sensitive.

{dataframe_to_markdown(params_df)}

## Limitations

FuelCheck historical files appear to record price update events rather than complete daily market snapshots. Methods based only on same-day update events can miss stations that continued operating without updating. The reconstructed end-of-day panel reduces that omission but relies on forward-fill and staleness-cap assumptions. Cycle detection is exploratory and descriptive; it is not causal identification, collusion detection, or evidence of illegal market conduct.

"""
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    (DOCS_DIR / "research_decisions.md").write_text(text, encoding="utf-8")


def make_figures(
    daily_methods: pd.DataFrame,
    cycles_all: pd.DataFrame,
    turning_points: pd.DataFrame,
    daily_coverage: pd.DataFrame,
    config: AnalysisConfig = DEFAULT_CONFIG,
) -> None:
    OUTPUT_FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    daily_methods = daily_methods.copy()
    daily_methods["date"] = pd.to_datetime(daily_methods["date"])

    primary = daily_methods.loc[daily_methods["method"] == config.selected_method].sort_values("date")
    primary_cycles = cycles_all.loc[cycles_all["method"] == config.selected_method] if not cycles_all.empty else pd.DataFrame()
    primary_turns = turning_points.loc[turning_points["method"] == config.selected_method] if not turning_points.empty else pd.DataFrame()

    plt.figure(figsize=(13, 6))
    plt.plot(primary["date"], primary["daily_price"], label=config.selected_method, linewidth=1.7)
    if not primary_turns.empty:
        troughs = primary_turns.loc[primary_turns["turning_type"] == "trough"]
        peaks = primary_turns.loc[primary_turns["turning_type"] == "peak"]
        plt.scatter(pd.to_datetime(troughs["date"]), troughs["price"], marker="v", color="#1f77b4", label="Detected troughs")
        plt.scatter(pd.to_datetime(peaks["date"]), peaks["price"], marker="^", color="#d62728", label="Detected peaks")
    plt.title("Sydney U91 daily price series with detected turning points")
    plt.xlabel("Date")
    plt.ylabel("Price (cents per litre)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_FIGURES_DIR / "daily_price_series_with_cycles.png", dpi=200)
    plt.close()

    plt.figure(figsize=(13, 6))
    for method, group in daily_methods.groupby("method"):
        plt.plot(group["date"], group["daily_price"], linewidth=1.2, label=method)
    plt.title("Sydney U91 daily price aggregation method comparison")
    plt.xlabel("Date")
    plt.ylabel("Price (cents per litre)")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(OUTPUT_FIGURES_DIR / "daily_aggregation_methods_comparison.png", dpi=200)
    plt.close()

    coverage = daily_methods.pivot(index="date", columns="method", values="coverage_rate")
    plt.figure(figsize=(13, 5))
    for method in coverage.columns:
        plt.plot(coverage.index, coverage[method], linewidth=1.1, label=method)
    plt.title("Sydney U91 daily station coverage by aggregation method")
    plt.xlabel("Date")
    plt.ylabel("Station coverage rate")
    plt.ylim(0, 1.05)
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(OUTPUT_FIGURES_DIR / "daily_station_coverage.png", dpi=200)
    plt.close()

    plt.figure(figsize=(8, 5))
    if not primary_cycles.empty:
        plt.scatter(
            primary_cycles["total_duration_days"],
            primary_cycles["rise_amplitude_cpl"],
            s=55,
            label="Rise amplitude",
        )
        plt.scatter(
            primary_cycles["total_duration_days"],
            primary_cycles["decline_amplitude_cpl"],
            s=55,
            label="Decline amplitude",
        )
    plt.title("Detected Sydney U91 cycle amplitude and duration")
    plt.xlabel("Total duration (days)")
    plt.ylabel("Amplitude (cents per litre)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_FIGURES_DIR / "cycle_amplitude_duration.png", dpi=200)
    plt.close()


def save_outputs(
    clean_events: pd.DataFrame,
    quality_summary: pd.DataFrame,
    update_distribution: pd.DataFrame,
    daily_coverage: pd.DataFrame,
    daily_methods: pd.DataFrame,
    eod_staleness: pd.DataFrame,
    eod_sensitivity: pd.DataFrame,
    cycles_all: pd.DataFrame,
    turning_points: pd.DataFrame,
    params_df: pd.DataFrame,
    config: AnalysisConfig = DEFAULT_CONFIG,
) -> dict[str, Path]:
    ensure_directories()
    paths = {
        "daily_price_methods": PROCESSED_DIR / "daily_price_methods.csv",
        "clean_events": PROCESSED_DIR / "clean_sydney_u91_events.csv",
        "data_quality_summary": TABLES_DIR / "data_quality_summary.csv",
        "station_day_update_distribution": TABLES_DIR / "station_day_update_distribution.csv",
        "daily_active_station_coverage": TABLES_DIR / "daily_active_station_coverage.csv",
        "eod_staleness_by_day": TABLES_DIR / "eod_staleness_by_day.csv",
        "eod_staleness_sensitivity": TABLES_DIR / "eod_staleness_sensitivity.csv",
        "cycle_metrics": TABLES_DIR / "cycle_metrics.csv",
        "turning_points": TABLES_DIR / "turning_points.csv",
        "cycle_detection_parameters": TABLES_DIR / "cycle_detection_parameters.csv",
        "robustness_comparison": TABLES_DIR / "robustness_comparison.csv",
    }
    clean_events.to_csv(paths["clean_events"], index=False)
    daily_methods.to_csv(paths["daily_price_methods"], index=False)
    quality_summary.to_csv(paths["data_quality_summary"], index=False)
    update_distribution.to_csv(paths["station_day_update_distribution"], index=False)
    daily_coverage.to_csv(paths["daily_active_station_coverage"], index=False)
    eod_staleness.to_csv(paths["eod_staleness_by_day"], index=False)
    eod_sensitivity.to_csv(paths["eod_staleness_sensitivity"], index=False)
    cycles_all.to_csv(paths["cycle_metrics"], index=False)
    turning_points.to_csv(paths["turning_points"], index=False)
    params_df.to_csv(paths["cycle_detection_parameters"], index=False)

    robustness = make_robustness_comparison(daily_methods, cycles_all, config)
    robustness.to_csv(paths["robustness_comparison"], index=False)
    write_markdown_table(
        TABLES_DIR / "robustness_comparison.md",
        "Robustness Comparison",
        "Daily aggregation methods are compared against the proposed primary specification.",
        robustness,
    )
    write_markdown_table(
        TABLES_DIR / "data_quality_summary.md",
        "Data Quality Summary",
        "Cleaning and audit checks are parameterised and counted before output generation.",
        quality_summary,
    )
    write_cycle_summary(cycles_all, params_df, config)
    write_research_decisions(robustness, eod_sensitivity, params_df, config)
    make_figures(daily_methods, cycles_all, turning_points, daily_coverage, config)
    return paths
