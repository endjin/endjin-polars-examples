# Running Polars on Microsoft Fabric: A Practical Guide

TL;DR:

# Overview

Microsoft Fabric's Python Notebooks provide an ideal environment for running Polars-based analytics workloads. With Polars pre-installed and native access to OneLake, you can build fast, memory-efficient data pipelines without the overhead of Spark. This post walks through the practicalities: reading raw files, transforming data, and writing to Delta tables in your Lakehouse.

Key points:

- **Reading files**: Use relative paths (`/lakehouse/default/Files/...`) for the pinned lakehouse, or ABFS paths for cross-workspace access
- **Reading Delta**: `pl.read_delta()` or `pl.scan_delta()` for lazy evaluation
- **Writing Delta**: `df.write_delta()` works out of the box; use `dt.replace_time_zone("UTC")` on timestamps to avoid SQL endpoint errors
- **Storage options**: Only needed for cross-lakehouse access—pass `{"bearer_token": notebookutils.credentials.getToken('storage'), "use_fabric_endpoint": "true"}`
- **Performance**: Use `scan_*` methods for large files, specify columns upfront, and consider tuning rowgroups (8M rows) for DirectLake consumption
- **Limitations**: No V-ORDER or Liquid Clustering without Spark; max 64 vCores on single node


## Why Polars on Fabric?

Fabric's new Python Notebooks run on a lightweight single-node container (2 vCores, 16GB RAM by default) rather than a Spark cluster. This is a better fit for many workloads:

- **Speed without complexity**: Polars' Rust-based engine delivers Spark-comparable performance on datasets that fit in memory, without the cluster coordination overhead.
- **Cost efficiency**: No Spark cluster spin-up means lower CU consumption for smaller jobs.
- **Rapid iteration**: Sub-second notebook startup times versus minutes for Spark.
- **Seamless integration**: Polars is pre-installed and OneLake paths work out of the box.

Microsoft explicitly recommends Polars (alongside DuckDB) as an alternative to pandas when you encounter memory pressure—a tacit acknowledgement that single-node, in-process tools have earned their place in the enterprise data stack.

## Getting Started

### Setting Up Your Environment

When you create a new Python Notebook in Fabric and pin it to a Lakehouse, you get immediate access to:

- Polars (currently v1.6 in the default environment)
- The `delta-rs` library for Delta Lake operations
- Native file system access to your Lakehouse via `/lakehouse/default/`

For files in the pinned Lakehouse, use relative paths:
```python
import polars as pl

# Files area
df = pl.read_csv("/lakehouse/default/Files/raw/sales.csv")

# Tables area (Delta)
df = pl.read_delta("/lakehouse/default/Tables/customers")
```

For cross-workspace or cross-lakehouse access, use ABFS paths:
```python
abfs_path = "abfss://WorkspaceName@onelake.dfs.fabric.microsoft.com/LakehouseName.Lakehouse"

# Reading from Files
df = pl.read_csv(f"{abfs_path}/Files/raw/sales.csv")

# Reading from Tables
df = pl.read_delta(f"{abfs_path}/Tables/customers")
```

> **Tip**: Replace spaces in workspace, lakehouse, folder, and file names with `%20` in ABFS paths.

## Reading Raw Data

### CSV Files

Polars excels at reading CSV files, with automatic type inference and parallel parsing:

```python
import polars as pl

# Single file from Files area
df = pl.read_csv("/lakehouse/default/Files/raw/transactions.csv")

# Multiple files with glob pattern
df = pl.read_csv("/lakehouse/default/Files/raw/transactions_*.csv")

# Large files: use scan for lazy evaluation
lf = pl.scan_csv("/lakehouse/default/Files/raw/large_file.csv")
df = lf.filter(pl.col("year") == 2024).collect()
```

For very large CSV files that might challenge memory, leverage lazy evaluation:

```python
# Only materialise what you need
result = (
    pl.scan_csv("/lakehouse/default/Files/raw/massive_file.csv")
    .filter(pl.col("region") == "EMEA")
    .group_by("product_category")
    .agg(pl.sum("revenue"))
    .collect()
)
```

### Excel Files

Polars reads Excel files using the `fastexcel` engine (based on Rust's Calamine library), which is significantly faster than alternatives:

```python
# Read first sheet
df = pl.read_excel("/lakehouse/default/Files/uploads/report.xlsx")

# Specific sheet
df = pl.read_excel(
    "/lakehouse/default/Files/uploads/report.xlsx",
    sheet_name="Q4 Sales"
)

# Skip header rows and specify columns
df = pl.read_excel(
    "/lakehouse/default/Files/uploads/messy_report.xlsx",
    sheet_name="Data",
    read_options={
        "skip_rows": 5,
        "header_row": 0
    }
)
```

> **Note**: For `.xls` files (legacy Excel format), you may need to use the `openpyxl` engine: `engine="openpyxl"`.

### Parquet Files

Parquet is Polars' natural habitat—the columnar format aligns perfectly with Polars' internal Arrow representation:

```python
# Direct read
df = pl.read_parquet("/lakehouse/default/Files/processed/sales.parquet")

# Lazy scan with predicate pushdown
df = (
    pl.scan_parquet("/lakehouse/default/Files/processed/sales_*.parquet")
    .filter(pl.col("sale_date") > "2024-01-01")
    .select(["customer_id", "product_id", "amount"])
    .collect()
)
```

## Data Transformation

Polars' composable expression API shines during transformation. Here's a typical ETL pattern:

```python
import polars as pl
from datetime import datetime

# Read raw data
raw_df = pl.read_csv("/lakehouse/default/Files/raw/orders.csv")

# Transform
transformed_df = (
    raw_df
    .with_columns([
        # Parse dates
        pl.col("order_date").str.to_date("%Y-%m-%d"),
        
        # Clean strings
        pl.col("customer_name").str.strip_chars().str.to_uppercase(),
        
        # Calculate derived columns
        (pl.col("quantity") * pl.col("unit_price")).alias("line_total"),
        
        # Add audit columns
        pl.lit(datetime.now()).alias("processed_at"),
        pl.lit("polars_etl").alias("processed_by")
    ])
    .filter(pl.col("line_total") > 0)
    .drop_nulls(subset=["customer_id"])
)
```

For operations across multiple columns, expressions can be applied in parallel:

```python
# Standardise all string columns
string_cols = [col for col in df.columns if df[col].dtype == pl.Utf8]

df = df.with_columns([
    pl.col(col).str.strip_chars().str.to_uppercase()
    for col in string_cols
])
```

## Writing to Delta Tables

### Basic Write

Writing a Polars DataFrame to a Delta table in the Tables area of your Lakehouse:

```python
# Write to Tables area
df.write_delta(
    "/lakehouse/default/Tables/processed_orders",
    mode="overwrite"
)
```

### Handling Timestamps

A common gotcha when writing Delta tables from Polars is timezone handling. Fabric's SQL endpoint expects timestamps with timezone information:

```python
# Convert timestamps to UTC before writing
df = df.with_columns([
    pl.col("order_date")
      .cast(pl.Datetime("us"))
      .dt.replace_time_zone("UTC")
      .alias("order_datetime")
])

df.write_delta(
    "/lakehouse/default/Tables/orders_with_timestamps",
    mode="overwrite"
)
```

### Write Modes

Polars supports standard Delta write modes:

```python
# Overwrite entire table
df.write_delta(path, mode="overwrite")

# Append to existing table
df.write_delta(path, mode="append")

# Error if table exists (default)
df.write_delta(path, mode="error")

# Ignore if table exists
df.write_delta(path, mode="ignore")

# Merge (upsert) - returns a TableMerger for chaining
(
    df.write_delta(
        path,
        mode="merge",
        delta_merge_options={
            "predicate": "source.id = target.id",
            "source_alias": "source",
            "target_alias": "target"
        }
    )
    .when_matched_update_all()
    .when_not_matched_insert_all()
    .execute()
)
```

### Using ABFS Paths with Storage Options

When writing to a different lakehouse or using ABFS paths, you'll need storage options:

```python
storage_options = {
    "bearer_token": notebookutils.credentials.getToken('storage'),
    "use_fabric_endpoint": "true"
}

df.write_delta(
    f"abfss://MyWorkspace@onelake.dfs.fabric.microsoft.com/MyLakehouse.Lakehouse/Tables/output_table",
    mode="overwrite",
    storage_options=storage_options
)
```

## Complete ETL Example

Here's a complete example that reads CSV files, transforms the data, and writes to a Delta table:

```python
import polars as pl
from datetime import datetime

# Configuration
INPUT_PATH = "/lakehouse/default/Files/raw/sales/"
OUTPUT_TABLE = "/lakehouse/default/Tables/fact_sales"

# Extract: Read all CSV files from landing zone
raw_df = pl.read_csv(
    f"{INPUT_PATH}*.csv",
    try_parse_dates=True
)

# Transform
fact_sales = (
    raw_df
    # Data quality: remove nulls and invalid records
    .drop_nulls(subset=["transaction_id", "customer_id"])
    .filter(pl.col("amount") > 0)
    
    # Business logic
    .with_columns([
        # Standardise customer IDs
        pl.col("customer_id").cast(pl.Utf8).str.zfill(10),
        
        # Calculate metrics
        (pl.col("amount") * pl.col("quantity")).alias("line_total"),
        (pl.col("amount") * pl.col("quantity") * pl.col("tax_rate")).alias("tax_amount"),
        
        # Date dimensions
        pl.col("sale_date").dt.year().alias("sale_year"),
        pl.col("sale_date").dt.month().alias("sale_month"),
        pl.col("sale_date").dt.weekday().alias("sale_day_of_week"),
        
        # Ensure timestamps are timezone-aware for Delta
        pl.col("sale_date")
          .cast(pl.Datetime("us"))
          .dt.replace_time_zone("UTC")
          .alias("sale_datetime"),
        
        # Audit columns
        pl.lit(datetime.now()).dt.replace_time_zone("UTC").alias("etl_processed_at"),
        pl.lit("polars_notebook").alias("etl_source")
    ])
    
    # Select final columns in order
    .select([
        "transaction_id",
        "customer_id", 
        "product_id",
        "sale_datetime",
        "sale_year",
        "sale_month",
        "sale_day_of_week",
        "quantity",
        "amount",
        "line_total",
        "tax_amount",
        "etl_processed_at",
        "etl_source"
    ])
)

# Load: Write to Delta table
fact_sales.write_delta(
    OUTPUT_TABLE,
    mode="overwrite"
)

print(f"Loaded {fact_sales.height:,} rows to {OUTPUT_TABLE}")
```

## Performance Optimisation Tips

### 1. Use Lazy Evaluation for Large Datasets

For datasets approaching memory limits, lazy evaluation lets Polars optimise the query plan:

```python
# Lazy: query optimiser kicks in
result = (
    pl.scan_csv("/lakehouse/default/Files/raw/huge_file.csv")
    .filter(pl.col("status") == "ACTIVE")
    .select(["id", "name", "value"])
    .collect()
)

# For very large results, use streaming
result = (
    pl.scan_csv("/lakehouse/default/Files/raw/huge_file.csv")
    .filter(pl.col("status") == "ACTIVE")
    .collect(streaming=True)
)
```

### 2. Read Only the Columns You Need

When working with wide tables, specify columns upfront:

```python
# CSV: only parse required columns
df = pl.read_csv(
    path,
    columns=["customer_id", "order_date", "amount"]
)

# Delta: projection pushdown handles this automatically with scan
df = (
    pl.scan_delta(delta_path)
    .select(["customer_id", "order_date", "amount"])
    .collect()
)
```

### 3. Leverage Delta's Predicate Pushdown

When reading Delta tables, filters can be pushed down to skip entire files:

```python
# The filter is pushed to the Delta scan
df = (
    pl.scan_delta("/lakehouse/default/Tables/partitioned_sales")
    .filter(pl.col("year") == 2024)
    .filter(pl.col("region") == "EMEA")
    .collect()
)
```

### 4. Optimise Rowgroups for DirectLake

If your Delta tables will be consumed by Power BI's DirectLake mode, configure larger rowgroups:

```python
from deltalake import WriterProperties

df.write_delta(
    "/lakehouse/default/Tables/powerbi_optimised",
    mode="overwrite",
    delta_write_options={
        "writer_properties": WriterProperties(
            compression="snappy"
        ),
        "min_rows_per_group": 8_000_000,
        "max_rows_per_group": 16_000_000,
        "max_rows_per_file": 48_000_000
    }
)
```

> **Note**: V-ORDER (Fabric's proprietary optimisation) isn't available outside Spark, but tuned rowgroups can achieve similar DirectLake performance in many cases.

### 5. Scale Up When Needed

For memory-intensive workloads, increase the compute allocation:

```python
%%configure
{
    "vCores": 8
}
```

Available configurations: 4, 8, 16, 32, or 64 vCores (memory scales proportionally).

## Useful Tools and Libraries

### msfabricutils

The [msfabricutils](https://github.com/mrjsj/msfabricutils) library provides Spark-free utilities specifically designed for Polars and delta-rs on Fabric:

```bash
%pip install msfabricutils
```

Features include:
- Simplified read/write operations with automatic authentication
- Common ETL transformations (audit columns, deduplication, etc.)
- Fabric API integration for workspace and lakehouse management
- Local development support with remote OneLake access

### Reading Delta Tables Lazily

For Delta tables larger than available memory:

```python
# Scan without loading into memory
lf = pl.scan_delta("/lakehouse/default/Tables/massive_table")

# Apply filters and aggregations
result = (
    lf
    .filter(pl.col("date") > "2024-01-01")
    .group_by("category")
    .agg(pl.sum("amount"))
    .collect()  # Only now materialises the result
)
```

## Current Limitations

A few things to be aware of:

- **V-ORDER**: Fabric's V-ORDER optimisation requires Spark; Polars-written Delta tables won't have this applied. Tuning rowgroups can partially compensate.
- **Liquid Clustering**: Similarly, Liquid Clustering is Spark-only.
- **Polars version**: The pre-installed version may lag behind the latest release. You can upgrade with `%pip install polars --upgrade`, though this adds notebook startup time.
- **Memory ceiling**: The maximum single-node configuration is 64 vCores. Beyond that, you'll need Spark or Polars Cloud (when available).

## References

- [Microsoft Learn: Python experience on Notebook](https://learn.microsoft.com/en-us/fabric/data-engineering/using-python-experience-on-notebook)
- [Microsoft Learn: Choosing Between Python and PySpark Notebooks](https://learn.microsoft.com/en-us/fabric/data-engineering/fabric-notebook-selection-guide)
- [Polars Documentation: Delta Lake](https://docs.pola.rs/user-guide/io/delta/)
- [delta-rs Documentation](https://delta-io.github.io/delta-rs/)
- [Sandeep Pawar: Working With Delta Tables in Fabric Python Notebook Using Polars](https://fabric.guru/working-with-delta-tables-in-fabric-python-notebook-using-polars)
- [Sandeep Pawar: Delta Lake Tables for Optimal DirectLake Performance](https://fabric.guru/delta-lake-tables-for-optimal-direct-lake-performance-in-fabric-python-notebook)
- [msfabricutils on GitHub](https://github.com/mrjsj/msfabricutils)
- [djouallah/Fabric_Notebooks_Demo](https://github.com/djouallah/Fabric_Notebooks_Demo)

## Summary

Polars on Microsoft Fabric offers a compelling alternative to Spark for many data engineering workloads. The combination of Polars' performance, Fabric's native OneLake integration, and the cost efficiency of single-node compute creates a practical path for teams who want enterprise-grade data pipelines without the complexity of distributed systems.

Start small, measure your workloads, and scale to Spark only when you genuinely need distributed compute. For many teams, that day may never come.
