from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from datetime import date
from pathlib import Path
from typing import Iterable

import pandas as pd

from .config import DEFAULT_CONFIG, RAW_CACHE_DIR, RAW_DIR, AnalysisConfig, ensure_directories


FUELCHECK_PACKAGE_API = (
    "https://data.nsw.gov.au/data/api/3/action/package_show"
    "?id=a97a46fc-2bdd-4b90-ac7f-0cb1e8d7ac3b"
)
DATASET_URL = "https://data.nsw.gov.au/data/dataset/fuel-check"
LICENSE_NOTE = (
    "NSW Data FuelCheck resources list Creative Commons Attribution Share-Alike. "
    "Reuse should attribute the NSW Government/Data.NSW source and follow the listed licence."
)

MONTH_NAME_TO_NUMBER = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}

COLUMN_ALIASES = {
    "station_id": ("ServiceStationID", "ServiceStationId", "StationID", "StationId"),
    "station_name": ("ServiceStationName", "StationName", "Name"),
    "address": ("Address", "ServiceStationAddress"),
    "suburb": ("Suburb",),
    "postcode": ("Postcode", "PostCode"),
    "brand": ("Brand",),
    "fuel_type": ("FuelCode", "FuelType", "Fuel"),
    "timestamp": ("PriceUpdatedDate", "UpdatedDate", "PriceUpdated", "LastUpdated"),
    "price_cpl": ("Price", "PriceCentsPerLitre"),
    "latitude": ("Latitude", "Lat"),
    "longitude": ("Longitude", "Long", "Lng"),
}


def required_months(config: AnalysisConfig = DEFAULT_CONFIG) -> list[tuple[int, int]]:
    """Return inclusive buffer and analysis months as (year, month)."""
    start = pd.Timestamp(config.buffer_start).to_period("M")
    end = pd.Timestamp(config.analysis_end).to_period("M")
    return [(p.year, p.month) for p in pd.period_range(start, end, freq="M")]


def _request_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def fetch_fuelcheck_package() -> dict:
    payload = _request_json(FUELCHECK_PACKAGE_API)
    if not payload.get("success"):
        raise RuntimeError("Data.NSW package_show did not return success=true.")
    return payload["result"]


def _parse_resource_month(resource: dict) -> tuple[int, int] | None:
    text = f"{resource.get('name') or ''} {resource.get('url') or ''}".lower()
    if "price history" not in text and "pricehistory" not in text:
        return None

    year_match = re.search(r"20\d{2}", text)
    if not year_match:
        return None
    year = int(year_match.group(0))

    month = None
    for name, number in MONTH_NAME_TO_NUMBER.items():
        if re.search(rf"\b{name}\b", text) or name in text.split("/")[-1]:
            month = number
            break
    if month is None:
        return None
    return year, month


def select_resources_for_period(
    package: dict, config: AnalysisConfig = DEFAULT_CONFIG
) -> tuple[list[dict], list[tuple[int, int]]]:
    wanted = set(required_months(config))
    by_month: dict[tuple[int, int], dict] = {}
    for resource in package.get("resources", []):
        parsed = _parse_resource_month(resource)
        if parsed in wanted:
            by_month[parsed] = resource
    missing = sorted(wanted - set(by_month))
    resources = [by_month[key] | {"covered_year": key[0], "covered_month": key[1]} for key in sorted(by_month)]
    return resources, missing


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_resource(resource: dict, raw_cache_dir: Path = RAW_CACHE_DIR) -> Path:
    raw_cache_dir.mkdir(parents=True, exist_ok=True)
    url = resource["url"]
    filename = url.rstrip("/").split("/")[-1]
    path = raw_cache_dir / filename
    expected_size = int(resource.get("size") or 0)
    if path.exists() and (expected_size == 0 or path.stat().st_size == expected_size):
        return path

    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=180) as response, path.open("wb") as handle:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            handle.write(chunk)
    return path


def build_source_manifest(
    resources: Iterable[dict],
    local_paths: Iterable[Path],
    config: AnalysisConfig = DEFAULT_CONFIG,
    access_date: str | None = None,
) -> pd.DataFrame:
    access_date = access_date or date.today().isoformat()
    analysis_start = pd.Timestamp(config.analysis_start).date()
    rows = []
    for resource, path in zip(resources, local_paths):
        year = int(resource["covered_year"])
        month = int(resource["covered_month"])
        period = pd.Period(year=year, month=month, freq="M")
        rows.append(
            {
                "official_source_url": resource.get("url"),
                "dataset_url": DATASET_URL,
                "access_date": access_date,
                "covered_period": str(period),
                "file_name": path.name,
                "local_path": path.relative_to(RAW_DIR.parent).as_posix(),
                "file_size": path.stat().st_size,
                "sha256": sha256_file(path),
                "resource_id": resource.get("id"),
                "resource_title": resource.get("name"),
                "resource_format": resource.get("format") or path.suffix.lstrip(".").upper(),
                "resource_last_modified": resource.get("last_modified") or resource.get("metadata_modified"),
                "licensing_reuse_note": LICENSE_NOTE,
                "analysis_role": "buffer" if period.end_time.date() < analysis_start else "analysis",
            }
        )
    return pd.DataFrame(rows)


def ensure_source_files(
    config: AnalysisConfig = DEFAULT_CONFIG, download: bool = True
) -> tuple[pd.DataFrame, list[str]]:
    ensure_directories()
    package = fetch_fuelcheck_package()
    resources, missing_months = select_resources_for_period(package, config)
    if missing_months:
        missing = [f"{year}-{month:02d}" for year, month in missing_months]
        return pd.DataFrame(), missing

    local_paths = []
    missing_downloads = []
    for resource in resources:
        filename = resource["url"].rstrip("/").split("/")[-1]
        path = RAW_CACHE_DIR / filename
        if not path.exists() and not download:
            missing_downloads.append(filename)
            continue
        local_paths.append(download_resource(resource) if download else path)

    if missing_downloads:
        return pd.DataFrame(), missing_downloads

    manifest = build_source_manifest(resources, local_paths, config)
    manifest.to_csv(RAW_DIR / "source_manifest.csv", index=False)
    return manifest, []


def _read_source_file(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".xls", ".xlsx"}:
        return pd.read_excel(path)
    raise ValueError(f"Unsupported raw data file type: {path}")


def load_raw_history(manifest: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for _, row in manifest.iterrows():
        path = RAW_DIR.parent / row["local_path"]
        df = _read_source_file(path)
        df["source_file"] = row["file_name"]
        df["source_period"] = row["covered_period"]
        df["analysis_role"] = row["analysis_role"]
        frames.append(df)
    if not frames:
        raise FileNotFoundError("No FuelCheck source files were available to load.")
    return pd.concat(frames, ignore_index=True)


def _find_column(columns: Iterable[str], canonical_name: str) -> str | None:
    normalised = {str(column).strip().lower(): column for column in columns}
    for alias in COLUMN_ALIASES[canonical_name]:
        match = normalised.get(alias.lower())
        if match is not None:
            return match
    return None


def _series_or_na(raw: pd.DataFrame, column: str | None) -> pd.Series:
    if column is None:
        return pd.Series(pd.NA, index=raw.index)
    return raw[column]


def _normalise_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return " ".join(str(value).strip().upper().split())


def parse_fuelcheck_timestamp(values: pd.Series, config: AnalysisConfig = DEFAULT_CONFIG) -> pd.Series:
    raw = values.astype("string").str.strip()
    iso_mask = raw.str.match(r"^\d{4}-\d{1,2}-\d{1,2}", na=False)
    parsed = pd.Series(pd.NaT, index=values.index, dtype="datetime64[ns]")
    parsed.loc[iso_mask] = pd.to_datetime(raw.loc[iso_mask], errors="coerce", format="mixed", dayfirst=False)
    parsed.loc[~iso_mask] = pd.to_datetime(raw.loc[~iso_mask], errors="coerce", format="mixed", dayfirst=True)
    if parsed.dt.tz is None:
        return parsed.dt.tz_localize(config.timezone, nonexistent="shift_forward", ambiguous="NaT")
    return parsed.dt.tz_convert(config.timezone)


def _derive_station_id(row: pd.Series) -> str | pd.NA:
    parts = [
        _normalise_text(row.get("station_name")),
        _normalise_text(row.get("address")),
        _normalise_text(row.get("suburb")),
        _normalise_text(row.get("postcode")),
        _normalise_text(row.get("brand")),
    ]
    if not any(parts[:2]):
        return pd.NA
    key = "|".join(parts)
    return "derived_" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def standardize_fuelcheck_columns(raw: pd.DataFrame, config: AnalysisConfig = DEFAULT_CONFIG) -> tuple[pd.DataFrame, dict]:
    columns = {name: _find_column(raw.columns, name) for name in COLUMN_ALIASES}
    out = pd.DataFrame(index=raw.index)
    out["source_file"] = raw.get("source_file")
    out["source_period"] = raw.get("source_period")
    out["analysis_role"] = raw.get("analysis_role")
    out["raw_station_id"] = _series_or_na(raw, columns["station_id"])
    out["station_name"] = _series_or_na(raw, columns["station_name"]).astype("string").str.strip()
    out["address"] = _series_or_na(raw, columns["address"]).astype("string").str.strip()
    out["suburb"] = _series_or_na(raw, columns["suburb"]).astype("string").str.strip()
    out["postcode"] = pd.to_numeric(_series_or_na(raw, columns["postcode"]), errors="coerce")
    out["brand"] = _series_or_na(raw, columns["brand"]).astype("string").str.strip()
    out["fuel_type"] = _series_or_na(raw, columns["fuel_type"]).astype("string").str.strip().str.upper()
    out["price_cpl"] = pd.to_numeric(_series_or_na(raw, columns["price_cpl"]), errors="coerce")
    out["timestamp"] = parse_fuelcheck_timestamp(_series_or_na(raw, columns["timestamp"]), config)
    out["date"] = out["timestamp"].dt.date
    out["latitude"] = pd.to_numeric(_series_or_na(raw, columns["latitude"]), errors="coerce")
    out["longitude"] = pd.to_numeric(_series_or_na(raw, columns["longitude"]), errors="coerce")

    explicit_station_id = out["raw_station_id"].astype("string").str.strip()
    out["station_id"] = explicit_station_id.mask(explicit_station_id.isna() | (explicit_station_id == ""))
    missing_explicit = out["station_id"].isna().sum()
    derived = out.apply(_derive_station_id, axis=1)
    out["station_id"] = out["station_id"].fillna(derived)

    audit = {
        "explicit_station_id_column": columns["station_id"] or "",
        "missing_explicit_station_id_rows": int(missing_explicit),
        "derived_station_id_rows": int(out["raw_station_id"].isna().sum()),
        "missing_derived_station_id_rows": int(out["station_id"].isna().sum()),
        "latitude_column": columns["latitude"] or "",
        "longitude_column": columns["longitude"] or "",
    }
    return out, audit


def clean_fuelcheck_events(
    raw: pd.DataFrame, config: AnalysisConfig = DEFAULT_CONFIG
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    standardised, column_audit = standardize_fuelcheck_columns(raw, config)
    audit_rows = [
        {"metric": "raw_rows", "value": len(standardised), "notes": "All loaded buffer and analysis rows."},
        {
            "metric": "missing_explicit_station_id_rows",
            "value": column_audit["missing_explicit_station_id_rows"],
            "notes": "Historical files reviewed here do not expose an official station id field; station_id is derived from station name, address, suburb, postcode and brand.",
        },
        {
            "metric": "missing_derived_station_id_rows",
            "value": column_audit["missing_derived_station_id_rows"],
            "notes": "Rows without enough station text to derive a stable station identifier.",
        },
        {
            "metric": "invalid_timestamp_rows",
            "value": int(standardised["timestamp"].isna().sum()),
            "notes": "Dropped before daily aggregation.",
        },
        {
            "metric": "missing_price_rows",
            "value": int(standardised["price_cpl"].isna().sum()),
            "notes": "Dropped before daily aggregation.",
        },
        {
            "metric": "missing_postcode_rows",
            "value": int(standardised["postcode"].isna().sum()),
            "notes": "Dropped before geographic filtering.",
        },
    ]

    valid = standardised.dropna(subset=["station_id", "timestamp", "date", "price_cpl", "postcode"]).copy()
    u91_labels = {label.upper() for label in config.fuel_labels_u91}
    non_u91 = ~valid["fuel_type"].isin(u91_labels)
    audit_rows.append({"metric": "non_u91_rows", "value": int(non_u91.sum()), "notes": "Filtered out; only U91-compatible labels are retained."})
    valid = valid.loc[~non_u91].copy()

    out_of_postcode = ~valid["postcode"].between(config.sydney_postcode_min, config.sydney_postcode_max)
    audit_rows.append(
        {
            "metric": "outside_configured_postcode_rows",
            "value": int(out_of_postcode.sum()),
            "notes": f"Configured operational Sydney range is {config.sydney_postcode_min}-{config.sydney_postcode_max}; this is not a strict metropolitan boundary.",
        }
    )
    valid = valid.loc[~out_of_postcode].copy()

    extreme = ~valid["price_cpl"].between(config.min_price_cpl, config.max_price_cpl)
    audit_rows.append(
        {
            "metric": "impossible_or_extreme_price_rows",
            "value": int(extreme.sum()),
            "notes": f"Filtered using parameterised range [{config.min_price_cpl}, {config.max_price_cpl}] cents per litre.",
        }
    )
    valid = valid.loc[~extreme].copy()

    duplicate_cols = ["station_id", "fuel_type", "timestamp", "price_cpl", "source_file"]
    duplicate_mask = valid.duplicated(subset=duplicate_cols, keep="first")
    audit_rows.append(
        {
            "metric": "exact_duplicate_events",
            "value": int(duplicate_mask.sum()),
            "notes": "Dropped after reporting so exact repeated records do not double-count update events.",
        }
    )
    valid = valid.loc[~duplicate_mask].copy()

    analysis_start = pd.Timestamp(config.analysis_start).date()
    analysis_end = pd.Timestamp(config.analysis_end).date()
    valid["is_analysis_period"] = valid["date"].between(analysis_start, analysis_end)
    analysis = valid.loc[valid["is_analysis_period"]].copy()

    audit_rows.extend(
        [
            {"metric": "clean_buffer_and_analysis_events", "value": len(valid), "notes": "Rows available after cleaning and filtering."},
            {"metric": "clean_analysis_events", "value": len(analysis), "notes": "Rows inside final analysis period only."},
            {"metric": "analysis_start", "value": config.analysis_start, "notes": "Inclusive final analysis period start."},
            {"metric": "analysis_end", "value": config.analysis_end, "notes": "Inclusive final analysis period end."},
            {"metric": "unique_analysis_stations", "value": int(analysis["station_id"].nunique()), "notes": "Denominator used for station coverage rates."},
        ]
    )
    quality_summary = pd.DataFrame(audit_rows)

    station_day_counts = (
        analysis.groupby(["station_id", "date"], as_index=False)
        .agg(update_events=("price_cpl", "size"))
    )
    update_distribution = (
        station_day_counts["update_events"]
        .value_counts()
        .sort_index()
        .rename_axis("updates_per_station_day")
        .reset_index(name="station_days")
    )

    daily_coverage = (
        analysis.groupby("date", as_index=False)
        .agg(
            active_stations=("station_id", "nunique"),
            update_events=("price_cpl", "size"),
            mean_price_cpl=("price_cpl", "mean"),
        )
    )
    total_stations = max(int(analysis["station_id"].nunique()), 1)
    daily_coverage["coverage_rate"] = daily_coverage["active_stations"] / total_stations
    return valid, quality_summary, update_distribution, daily_coverage
