# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "jupyter",
# META     "jupyter_kernel_name": "python3.12"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "06134a22-d116-4be7-8a9d-91e39bc27141",
# META       "default_lakehouse_name": "HousePriceAnalytics",
# META       "default_lakehouse_workspace_id": "15c07add-854d-487a-bc6f-477e0b8798f6",
# META       "known_lakehouses": [
# META         {
# META           "id": "06134a22-d116-4be7-8a9d-91e39bc27141"
# META         }
# META       ]
# META     }
# META   }
# META }

# MARKDOWN ********************

# ## Import Polars

# CELL ********************

# pip install polars
# poetry add polars
# uv add polars

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

import polars as pl

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# MARKDOWN ********************

# ## Read Data into DataFrame

# CELL ********************

COLUMN_NAMES = [
        "id", "price", "date", "postcode", "property_type",
        "old_new", "duration", "paon", "saon", "street",
        "locality", "town_city", "district", "county",
        "ppd_category", "record_type",
    ]

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

# abfss://15c07add-854d-487a-bc6f-477e0b8798f6@onelake.dfs.fabric.microsoft.com/06134a22-d116-4be7-8a9d-91e39bc27141/Files/land_registry_data/pp-2015.csv

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

import notebookutils

land_registry_data = pl.read_csv(
    source="abfss://15c07add-854d-487a-bc6f-477e0b8798f6@onelake.dfs.fabric.microsoft.com/06134a22-d116-4be7-8a9d-91e39bc27141/Files/land_registry_data/pp-*.csv",
    has_header=False,
    new_columns=COLUMN_NAMES,
    infer_schema=True,
    null_values=[""],
    storage_options={
        "bearer_token": notebookutils.credentials.getToken("storage"),
        "use_fabric_endpoint": "true",
    }            
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

land_registry_data

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

land_registry_data.describe()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

land_registry_data = (
    land_registry_data
    .with_columns(
        pl.col("date").str.to_date(format="%Y-%m-%d %H:%M"),
    )
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# MARKDOWN ********************

# ## Clean Up The Data

# CELL ********************

land_registry_data = land_registry_data.with_columns(
    pl.col("property_type").replace({
        "D": "Detached",
        "S": "Semi-Detached",
        "T": "Terraced",
        "F": "Flat",
        "O": "Other",
    }).alias("property_type")
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

land_registry_data["property_type"].value_counts()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

land_registry_data = land_registry_data.filter(pl.col("property_type") != "Other")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# MARKDOWN ********************

# ## Add new features

# CELL ********************

land_registry_data = (
    land_registry_data
    .with_columns(
        pl.col("date").dt.year().alias("year"),
    )
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

annual_median_price_by_property_type = (
    land_registry_data
    .group_by(["year", "property_type"])
    .agg(
        pl.col("price").median().alias("median_price")
    )
    .sort(["year", "property_type"])
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

annual_median_price_by_property_type

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# MARKDOWN ********************

# ## Visualise the results

# CELL ********************

import plotly.express as px

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

px.line(
    annual_median_price_by_property_type,
    x="year",
    y="median_price",
    color="property_type",
    markers=True,
    title="Median Price by Year and Property Type",
    width=800,
    height=600,
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# MARKDOWN ********************

# ## Write data to Delta format

# CELL ********************

annual_median_price_by_property_type.write_delta("../../data/price_paid_insights/annual_price_by_property_type", mode="overwrite")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# MARKDOWN ********************

# ## Lazy Frames

# CELL ********************

lazy_frame = (
    pl.scan_csv(
    source="../../data/land_registry_data/pp-*.csv",
    has_header=False,
    new_columns=COLUMN_NAMES,
    infer_schema=False,
    null_values=[""])
    .with_columns(
        pl.col("date").str.to_date(format="%Y-%m-%d %H:%M"),
    )
    .with_columns(
        pl.col("property_type").replace({
            "D": "Detached",
            "S": "Semi-Detached",
            "T": "Terraced",
            "F": "Flat",
            "O": "Other",
        }).alias("property_type")
    )
    .filter(pl.col("property_type") != "Other")
    .with_columns(
        pl.col("date").dt.year().alias("year")
    )
    .group_by(["year", "property_type"])
    .agg(
        pl.col("price").median().alias("median_price")
    )
    .sort(["year", "property_type"])
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

lazy_frame

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

print(lazy_frame.explain())

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

lazy_frame.collect()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }
