# Architecture

## Overview

The project is organised as a Python monorepo with two local packages under `src/`, a BDD test suite, and Jupyter notebooks grouped by audience.

```
src/
  data_importers/         Downloads raw data from external sources
  data_wrangler/          Polars transformation pipeline + Pandera schema

notebooks/
  sqlbits_2026/           SQLbits 2026 conference demos (Land Registry)
  polars_blog/            Polars blog post series

tests/
  bdd/
    features/             Gherkin .feature files — one per behaviour
    steps/                Behave step definitions
    test_data/            100-row CSV sample used by @e2e tests

skills/                   How-to guides for working in this codebase
data/
  land_registry_data/     Downloaded yearly CSVs (gitignored)
```

## Data flow

```
Land Registry S3
      │
      ▼
LandRegistryImporter.download_land_registry_data()
      │  writes pp-{year}.csv to data/land_registry_data/
      ▼
DataWrangler.load_data(data_folder)
      │  pl.scan_csv — lazy, names 16 columns, casts price + date
      ▼
drop / filter / rename / extract steps (lazy)
      ▼
DataWrangler.summarise_by_year_and_property_type()
      │  group_by year + property_type
      ▼
DataWrangler.sort_by_year_and_property_type()
      ▼
.collect()  →  pl.DataFrame
      │
      ▼
Plotly chart in summarise_land_registry_data.ipynb
```

## Key design decisions

### Lazy execution throughout the pipeline

`load_data` returns a `pl.LazyFrame` via `scan_csv`. All transformation static methods accept `DataFrame | LazyFrame` (`FrameType`), so they compose transparently in both the lazy pipeline and eager unit tests. `collect()` is called once at the very end of `run_pipeline`, letting Polars optimise the entire query plan.

### DataWrangler as a class of static methods

Each transformation is a `@staticmethod` so it can be called individually in unit tests (`DataWrangler.rename_property_type(df)`) or composed via `.pipe()` in the pipeline. `load_data` and `run_pipeline` are the only methods that need class state, so they are `@staticmethod` and `@classmethod` respectively.

### Single Pandera schema

`price_paid_data_schema` in `schema_price_paid_data.py` validates all 16 Land Registry columns. There is no separate "raw" schema — validation happens on the full schema after loading.

### BDD tests as executable specifications

Every public method on `DataWrangler` has a corresponding `.feature` file. Unit tests (`@unit`) use in-memory `pl.DataFrame` tables defined inline in Gherkin. The end-to-end test (`@e2e`) runs `run_pipeline` against a 100-row sample CSV in `tests/bdd/test_data/`.
