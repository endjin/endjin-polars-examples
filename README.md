# endjin-polars-examples
endjin-polars-examples is a series of runnable notebooks and companion scripts that explore how to work with the [Polars](https://www.pola.rs/) DataFrame engine. The goal is to highlight idiomatic ways to ingest, transform, inspect, and summarize data while leaning on Polars' lazy execution, expression system, and columnar performance.

## Dataset
We demonstrate the techniques using the publicly available World Bank Open Data API. Specifically, we download the **World Bank Indicators** dataset, which contains macroeconomic series (GDP, population, education, etc.) for every country and year. The raw exports live under `data/world_bank/` and include:

- CSV extracts that mirror the API's standard download format (`csv/countries.csv`, `csv/data.csv`, and `csv/indicators.csv`).
- JSON files for the data snapshots per year (`json/data_XXXX.json`).
- Parquet and DuckDB snapshots for faster reads (`parquet/`, `duckdb/world_bank.db.wal`).

You can explore the original API documentation and download options here:
- World Bank Open Data main page: https://data.worldbank.org/
- Indicator query and API docs: https://datahelpdesk.worldbank.org/knowledgebase/articles/889386-developer-information-overview

## Project layout
- `notebooks/` contains narrative Polars tutorials (the `polars-blog-part-*` series) that walk through DataFrame creation, cleaning, filtering, joins, and aggregation.
- `src/data_importers/` holds reusable scripts for fetching or reshaping the World Bank data before feeding it into Polars-powered notebooks.
- `docs/` documents conceptual guides and blog drafts describing implementation details and translation strategies.
- `data/world_bank/` stores the dataset in multiple formats so readers can experiment with CSV, JSON, Parquet, and DuckDB access patterns.

## Prerequisites
To work comfortably with this repository you should have the following tools installed:
1. Visual Studio Code (https://code.visualstudio.com/) with a Python or Polars-friendly extension (e.g., the Official Python extension) so you can edit notebooks and scripts interactively.
2. Docker (https://www.docker.com/) to reproduce builds or run containerized environments if you prefer isolating tooling (the repo should be runnable without Docker, but it helps when matching the upstream development container).
3. Git (https://git-scm.com/) to clone the repository, track changes, and share contributions.

## Getting started
1. Clone the repo and open it in VS Code.
2. Activate the provided Python environment (via `uv` in this notebook, or another virtual environment that includes Polars).
3. Open `notebooks/polars-blog-part-4.ipynb` (and its siblings) to run the cells interactively; the notebook shows both eager and lazy patterns.
4. Use the scripts under `src/data_importers/` to refresh the World Bank dataset if you need more recent data.

That’s it—Polars’ next-generation performance makes these examples snappy even when the World Bank tables grow large, and the notebooks explain each operator in context.
