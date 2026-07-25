from __future__ import annotations

import sys
from pathlib import Path

from .config import DEFAULT_CONFIG, AnalysisConfig, ensure_directories
from .construct_daily_prices import construct_daily_price_methods
from .detect_cycles import CycleDetectionParams, detect_cycles_for_methods
from .load_and_clean import (
    DATASET_URL,
    clean_fuelcheck_events,
    ensure_source_files,
    load_raw_history,
)
from .make_outputs import save_outputs


def run(config: AnalysisConfig = DEFAULT_CONFIG, download: bool = True) -> dict:
    ensure_directories()
    manifest, missing = ensure_source_files(config, download=download)
    if missing:
        missing_text = ", ".join(missing)
        raise RuntimeError(
            "Official FuelCheck data could not be obtained for: "
            f"{missing_text}. Download from {DATASET_URL}, place the files under "
            "data/raw/fuelcheck_history/, then run `python -m src.run_analysis`."
        )

    raw = load_raw_history(manifest)
    clean_events, quality_summary, update_distribution, daily_coverage = clean_fuelcheck_events(raw, config)
    daily_methods, eod_staleness, eod_sensitivity = construct_daily_price_methods(clean_events, config)
    params = CycleDetectionParams.from_config(config)
    cycles_all, turning_points, params_df = detect_cycles_for_methods(daily_methods, params)
    paths = save_outputs(
        clean_events=clean_events,
        quality_summary=quality_summary,
        update_distribution=update_distribution,
        daily_coverage=daily_coverage,
        daily_methods=daily_methods,
        eod_staleness=eod_staleness,
        eod_sensitivity=eod_sensitivity,
        cycles_all=cycles_all,
        turning_points=turning_points,
        params_df=params_df,
        config=config,
    )
    selected_cycles = cycles_all.loc[cycles_all["method"] == config.selected_method] if not cycles_all.empty else cycles_all
    return {
        "manifest": manifest,
        "raw_rows": len(raw),
        "clean_events": len(clean_events),
        "daily_methods": daily_methods,
        "cycles_all": cycles_all,
        "selected_cycle_count": len(selected_cycles),
        "paths": paths,
    }


def main() -> int:
    results = run()
    manifest = results["manifest"]
    print("FuelCheck cycle analysis complete.")
    print(f"Source months: {manifest['covered_period'].min()} to {manifest['covered_period'].max()}")
    print(f"Raw rows loaded: {results['raw_rows']}")
    print(f"Clean buffer+analysis U91 Sydney events: {results['clean_events']}")
    print(f"Daily methods written: {', '.join(sorted(results['daily_methods']['method'].unique()))}")
    print(f"Primary complete cycles detected: {results['selected_cycle_count']}")
    for name, path in results["paths"].items():
        print(f"{name}: {Path(path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
