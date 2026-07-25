# Raw FuelCheck Data

This directory retains original raw inputs without notebook-side moves or rewrites.

The full cycle-analysis workflow uses official NSW FuelCheck monthly price-history files from Data.NSW:

- Dataset page: https://data.nsw.gov.au/data/dataset/fuel-check
- Programmatic resource list: https://data.nsw.gov.au/data/api/3/action/package_show?id=a97a46fc-2bdd-4b90-ac7f-0cb1e8d7ac3b
- Licence shown by Data.NSW resources: Creative Commons Attribution Share-Alike

The analysis period is 2025-04-01 to 2026-03-31. The workflow also downloads March 2025 as a buffer month for finite end-of-day reconstruction, but buffer days are not included in final results.

Monthly source files are downloaded to `data/raw/fuelcheck_history/`, which is intentionally ignored by Git so large raw files are not committed. Source provenance for the locally used official files is written to `data/raw/source_manifest.csv`, including source URL, access date, covered period, file size and SHA-256 checksum.

To reproduce from the repository root:

```bash
python -m src.run_analysis
```

If automatic download is unavailable, manually download the required monthly FuelCheck Price History resources from Data.NSW and place them in `data/raw/fuelcheck_history/`, then rerun the command above. Do not replace missing official months with synthetic data.
