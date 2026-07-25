from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
RAW_CACHE_DIR = RAW_DIR / "fuelcheck_history"
PROCESSED_DIR = DATA_DIR / "processed"
DOCS_DIR = PROJECT_ROOT / "docs"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
TABLES_DIR = OUTPUTS_DIR / "tables"
OUTPUT_FIGURES_DIR = OUTPUTS_DIR / "figures"
LEGACY_FIGURES_DIR = PROJECT_ROOT / "figures"


@dataclass(frozen=True)
class AnalysisConfig:
    analysis_start: str = "2025-04-01"
    analysis_end: str = "2026-03-31"
    buffer_start: str = "2025-03-01"
    timezone: str = "Australia/Sydney"
    sydney_postcode_min: int = 2000
    sydney_postcode_max: int = 2234
    fuel_labels_u91: tuple[str, ...] = (
        "U91",
        "UNLEADED 91",
        "ULP",
        "REGULAR UNLEADED",
        "UNLEADED",
    )
    min_price_cpl: float = 50.0
    max_price_cpl: float = 350.0
    eod_staleness_cap_days: int = 7
    eod_sensitivity_caps: tuple[int, ...] = (3, 7, 14)
    smoothing_window: int = 7
    min_peak_prominence: float = 3.0
    min_distance_between_peaks: int = 14
    min_cycle_amplitude: float = 8.0
    min_cycle_duration_days: int = 10
    max_cycle_duration_days: int = 75
    turning_point_confirmation_window: int = 3
    selected_method: str = "reconstructed_eod_panel_cap7"
    parameter_set_name: str = "default_v1"


DEFAULT_CONFIG = AnalysisConfig()


def ensure_directories() -> None:
    for folder in [
        RAW_DIR,
        RAW_CACHE_DIR,
        PROCESSED_DIR,
        DOCS_DIR,
        TABLES_DIR,
        OUTPUT_FIGURES_DIR,
        LEGACY_FIGURES_DIR,
    ]:
        folder.mkdir(parents=True, exist_ok=True)
