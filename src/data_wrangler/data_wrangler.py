import polars as pl
from datetime import date
from typing import Literal, Protocol, runtime_checkable
from urllib.parse import quote

FrameType = pl.DataFrame | pl.LazyFrame
DeltaWriteMode = Literal["error", "append", "overwrite", "ignore"]


@runtime_checkable
class PricePaidDataSource(Protocol):
    """Abstraction for loading raw Price Paid data as a Polars lazy frame."""

    def scan_price_paid(self) -> pl.LazyFrame:
        """Return the raw dataset as a LazyFrame ready for transformation."""


class LocalCsvDataSource:
    """Loads Land Registry Price Paid CSV files from a local folder."""

    DEFAULT_OUTPUT_ROOT = "data/onelake"

    def __init__(
        self,
        data_folder: str,
        column_names: list[str],
        output_root: str | None = None,
    ) -> None:
        self.data_folder = data_folder
        self.column_names = column_names
        self.output_root = output_root or self.DEFAULT_OUTPUT_ROOT

    def scan_price_paid(self) -> pl.LazyFrame:
        return (
            pl.scan_csv(
                f"{self.data_folder}/pp-*.csv",
                has_header=False,
                new_columns=self.column_names,
                infer_schema_length=0,
                null_values=[""],
            )
            .with_columns(
                pl.col("price").cast(pl.Int64),
                pl.col("date").str.to_date(format="%Y-%m-%d %H:%M"),
            )
        )

    def write_to_table(
        self,
        df: pl.DataFrame,
        schema: str,
        table: str,
        mode: DeltaWriteMode = "overwrite",
    ) -> None:
        """
        Write a DataFrame to a local Delta table.

        Args:
            df: The DataFrame to write.
            schema: The schema (folder) name, e.g. 'silver'.
            table: The table name, e.g. 'price_paid_data'.
            mode: Write mode - 'error', 'append', 'overwrite', or 'ignore'.
        """
        from pathlib import Path

        table_path = Path(self.output_root) / schema / table
        table_path.mkdir(parents=True, exist_ok=True)

        df.write_delta(
            str(table_path),
            mode=mode,
        )


class OneLakeDataSourceBase:
    """Base class providing common OneLake utilities for Fabric data sources."""

    @staticmethod
    def construct_base_abfss_path(workspace_name: str, lakehouse_name: str) -> str:
        """Construct the base ABFSS path for a given workspace and lakehouse."""
        encoded_workspace = quote(workspace_name, safe="")
        encoded_lakehouse = quote(lakehouse_name, safe="")
        return f"abfss://{encoded_workspace}@onelake.dfs.fabric.microsoft.com/{encoded_lakehouse}.Lakehouse"

    @staticmethod
    def create_storage_options(token: str) -> dict:
        """Create storage options for authenticating with OneLake."""
        return {
            "bearer_token": token,
            "use_fabric_endpoint": "true",
        }


class OneLakeFabricDataSource(OneLakeDataSourceBase):
    """
    Loads Price Paid data from a Fabric Lakehouse when running inside a Fabric notebook.

    Uses notebookutils to obtain the authentication token automatically.
    """

    def __init__(
        self,
        workspace_name: str,
        lakehouse_name: str,
        file_pattern: str,
        column_names: list[str],
    ) -> None:
        self.workspace_name = workspace_name
        self.lakehouse_name = lakehouse_name
        self.file_pattern = file_pattern
        self.column_names = column_names

    def _get_token(self) -> str:
        """Obtain bearer token using Fabric notebookutils."""
        from notebookutils import mssparkutils  # type: ignore[import-not-found]

        return mssparkutils.credentials.getToken("storage")

    def scan_price_paid(self) -> pl.LazyFrame:
        base_path = self.construct_base_abfss_path(self.workspace_name, self.lakehouse_name)
        full_path = f"{base_path}/Files/{self.file_pattern}"
        storage_options = self.create_storage_options(self._get_token())

        return (
            pl.scan_csv(
                full_path,
                has_header=False,
                new_columns=self.column_names,
                infer_schema_length=0,
                null_values=[""],
                storage_options=storage_options,
            )
            .with_columns(
                pl.col("price").cast(pl.Int64),
                pl.col("date").str.to_date(format="%Y-%m-%d %H:%M"),
            )
        )

    def write_to_table(
        self,
        df: pl.DataFrame,
        schema: str,
        table: str,
        mode: DeltaWriteMode = "overwrite",
    ) -> None:
        """
        Write a DataFrame to a Fabric Lakehouse Delta table.

        Args:
            df: The DataFrame to write.
            schema: The schema name, e.g. 'silver'.
            table: The table name, e.g. 'price_paid_data'.
            mode: Write mode - 'error', 'append', 'overwrite', or 'ignore'.
        """
        base_path = self.construct_base_abfss_path(self.workspace_name, self.lakehouse_name)
        table_path = f"{base_path}/Tables/{schema}/{table}"
        storage_options = self.create_storage_options(self._get_token())

        df.write_delta(
            table_path,
            mode=mode,
            storage_options=storage_options,
        )


class DataWrangler:

    COLUMN_NAMES = [
        "id", "price", "date", "postcode", "property_type",
        "old_new", "duration", "paon", "saon", "street",
        "locality", "town_city", "district", "county",
        "ppd_category", "record_type",
    ]

    DEFAULT_SILVER_SCHEMA = "silver"
    DEFAULT_SILVER_TABLE = "price_paid_data"
    DEFAULT_GOLD_SCHEMA = "gold"

    def __init__(self, data_source: PricePaidDataSource) -> None:
        self.data_source = data_source

    @classmethod
    def run_pipeline_with_data_source(
        cls,
        data_source: PricePaidDataSource,
        schema: str | None = None,
        table: str | None = None,
        write_mode: DeltaWriteMode = "overwrite",
    ) -> pl.DataFrame:
        """
        Runs the full transformation pipeline using an injected data source,
        then writes the cleaned result to the silver layer.

        Args:
            data_source: The data source to read from and write to.
            schema: Target schema name (default: 'silver').
            table: Target table name (default: 'price_paid_data').
            write_mode: Write mode - 'error', 'append', 'overwrite', or 'ignore'.

        Returns:
            The transformed DataFrame.
        """
        return cls(data_source).process_to_silver(
            schema=schema,
            table=table,
            write_mode=write_mode,
        )

    def process_to_silver(
        self,
        schema: str | None = None,
        table: str | None = None,
        write_mode: DeltaWriteMode = "overwrite",
    ) -> pl.DataFrame:
        """
        Runs the full cleaning and feature engineering pipeline against the
        configured data source and writes the result to the silver layer.

        This produces a full-fidelity dataset with all cleaning and feature
        engineering applied, but no aggregation.

        Args:
            schema: Target schema name (default: 'silver').
            table: Target table name (default: 'price_paid_data').
            write_mode: Write mode - 'error', 'append', 'overwrite', or 'ignore'.

        Returns:
            The cleaned and enriched DataFrame.
        """
        schema = schema or self.DEFAULT_SILVER_SCHEMA
        table = table or self.DEFAULT_SILVER_TABLE

        result = (
            self.data_source.scan_price_paid()
            .pipe(self.drop_records_without_postcode)
            .pipe(self.drop_records_without_date)
            .pipe(self.filter_other_property_types)
            .pipe(self.extract_year_from_date)
            .pipe(self.rename_property_type)
            .pipe(self.rename_duration)
            .pipe(self.rename_old_new)
            .pipe(self.extract_postcode_area)
            .collect()  # type: ignore[union-attr]
        )

        self.data_source.write_to_table(result, schema, table, mode=write_mode)  # type: ignore[union-attr]

        return result

    def process_to_gold(
        self,
        silver_data: pl.DataFrame,
        schema: str | None = None,
        write_mode: DeltaWriteMode = "overwrite",
    ) -> dict[str, pl.DataFrame]:
        """
        Processes silver layer data into gold layer dimensional model.

        Creates:
        - dim_date: Date dimension table spanning the data's date range
        - dim_location: Unique location hierarchy (county, district, town_city, postcode_area)
        - fact_price_paid: Core transaction facts with foreign keys to dimensions

        Args:
            silver_data: Cleaned price paid data from process_to_silver().
            schema: Target schema name (default: 'gold').
            write_mode: Write mode - 'error', 'append', 'overwrite', or 'ignore'.

        Returns:
            Dictionary containing 'dim_date', 'dim_location', and 'fact_price_paid' DataFrames.
        """
        schema = schema or self.DEFAULT_GOLD_SCHEMA

        # Build date dimension from data range
        min_date = silver_data.select(pl.col("date").min()).item()
        max_date = silver_data.select(pl.col("date").max()).item()
        dim_date = self.build_date_dimension(min_date, max_date)

        # Build location dimension
        dim_location = self.build_location_dimension(silver_data)

        # Build fact table
        fact_price_paid = self.build_price_paid_fact(silver_data)

        # Write all tables to gold schema
        self.data_source.write_to_table(dim_date, schema, "dim_date", mode=write_mode)  # type: ignore[union-attr]
        self.data_source.write_to_table(dim_location, schema, "dim_location", mode=write_mode)  # type: ignore[union-attr]
        self.data_source.write_to_table(fact_price_paid, schema, "fact_price_paid", mode=write_mode)  # type: ignore[union-attr]

        return {
            "dim_date": dim_date,
            "dim_location": dim_location,
            "fact_price_paid": fact_price_paid,
        }

    @staticmethod
    def build_date_dimension(min_date: date, max_date: date) -> pl.DataFrame:
        """
        Builds a date dimension table for the inclusive range [min_date, max_date].

        Args:
            min_date: First date in the range.
            max_date: Last date in the range (inclusive).

        Returns:
            DataFrame with columns: date, year, month, month_name, day, weekday,
            day_name, day_of_year, is_weekend, is_leap_year.
        """
        return (
            pl.date_range(start=min_date, end=max_date, interval="1d", eager=True)
            .to_frame(name="date")
            .with_columns(
                pl.col("date").dt.year().alias("year"),
                pl.col("date").dt.month().alias("month"),
                pl.col("date").dt.strftime("%B").alias("month_name"),
                pl.col("date").dt.day().alias("day"),
                pl.col("date").dt.weekday().alias("weekday"),
                pl.col("date").dt.strftime("%A").alias("day_name"),
                pl.col("date").dt.ordinal_day().alias("day_of_year"),
                (pl.col("date").dt.weekday() >= 6).alias("is_weekend"),
                pl.col("date").dt.is_leap_year().alias("is_leap_year"),
            )
        )

    @staticmethod
    def build_location_dimension(df: pl.DataFrame) -> pl.DataFrame:
        """
        Builds a location dimension from unique combinations of location fields.

        Args:
            df: DataFrame containing county, district, town_city, postcode_area columns.

        Returns:
            DataFrame with unique location combinations.
        """
        return (
            df.select(["county", "district", "town_city", "postcode_area"])
            .unique()
            .sort(["county", "district", "town_city", "postcode_area"])
        )

    @staticmethod
    def build_price_paid_fact(df: pl.DataFrame) -> pl.DataFrame:
        """
        Builds the price paid fact table with foreign keys to dimensions.

        Args:
            df: Full silver layer DataFrame.

        Returns:
            DataFrame with core transaction columns suitable for a fact table.
        """
        return df.select([
            "price",
            pl.col("date").alias("date_of_transfer"),  # FK to dim_date
            "postcode",
            "postcode_area",  # FK to dim_location
            "property_type",
            "old_new",
        ])

    @staticmethod
    def filter_other_property_types(df: FrameType) -> FrameType:
        """
        Filters the DataFrame to include only rows where property_type is not 'Other'.

        Args:
            df: Input frame with a column named 'property_type'.
        Returns:
            Frame containing only rows where property_type is not 'O'.
        """
        return df.filter(pl.col("property_type") != "O")

    @staticmethod
    def extract_year_from_date(df: FrameType) -> FrameType:
        """
        Extracts the year from the 'date' column and adds it as a new column 'year'.

        Args:
            df: Input frame with a column named 'date' of type Date.
        Returns:
            Frame with an additional integer column 'year'.
        """
        return df.with_columns(
            pl.col("date").dt.year().alias("year"),
        )

    @staticmethod
    def extract_postcode_area(df: FrameType) -> FrameType:
        """
        Extracts the postcode area (outward code) from the 'postcode' column using
        strict UK postcode validation. Returns null for any postcode that does not
        match the standard format.

        Args:
            df: Input frame with a column named 'postcode' of type String.
        Returns:
            Frame with an additional column 'postcode_area' (e.g. 'SW1A' from 'SW1A 2AA').
        """
        return df.with_columns(
            pl.col("postcode")
            .str.extract(r"^([A-Z]{1,2}[0-9R][0-9A-Z]?) [0-9][ABD-HJLNP-UW-Z]{2}$", 1)
            .alias("postcode_area")
        )

    @staticmethod
    def extract_postcode_district(df: FrameType) -> FrameType:
        """
        Extracts the postcode district from the 'postcode' column and adds it as a
        new column 'postcode_district' (e.g. 'SW1' from 'SW1A 2AA').

        Args:
            df: Input frame with a column named 'postcode' of type String.
        Returns:
            Frame with an additional column 'postcode_district'.
        """
        return df.with_columns(
            pl.col("postcode").str.extract(r"^([A-Z]{1,2}[0-9R][0-9A-Z]?)\s", 1).alias("postcode_district")
        )

    @staticmethod
    def drop_records_without_postcode(df: FrameType) -> FrameType:
        """
        Drops records where the 'postcode' column is null or empty.

        Args:
            df: Input frame with a column named 'postcode' of type String.
        Returns:
            Frame with only rows where postcode is present and non-empty.
        """
        return df.filter(pl.col("postcode").is_not_null() & (pl.col("postcode") != ""))

    @staticmethod
    def drop_records_without_date(df: FrameType) -> FrameType:
        """
        Drops records where the 'date' column is null.

        Args:
            df: Input frame with a column named 'date' of type Date.
        Returns:
            Frame with only rows where date is present.
        """
        return df.filter(pl.col("date").is_not_null())

    @staticmethod
    def rename_property_type(df: FrameType) -> FrameType:
        """
        Renames the values in the 'property_type' column to descriptive labels:
        D → Detached, S → Semi-Detached, T → Terraced, F → Flat, O → Other.

        Args:
            df: Input frame with a column named 'property_type' of type String.
        Returns:
            Frame with property_type values replaced by their full names.
        """
        return df.with_columns(
            pl.col("property_type").replace({
                "D": "Detached",
                "S": "Semi-Detached",
                "T": "Terraced",
                "F": "Flat",
                "O": "Other",
            })
        )

    @staticmethod
    def rename_duration(df: FrameType) -> FrameType:
        """
        Renames the values in the 'duration' column to descriptive labels:
        F → Freehold, L → Leasehold, U → Unknown.

        Args:
            df: Input frame with a column named 'duration' of type String.
        Returns:
            Frame with duration values replaced by their full names.
        """
        return df.with_columns(
            pl.col("duration").replace({
                "F": "Freehold",
                "L": "Leasehold",
                "U": "Unknown",
            })
        )

    @staticmethod
    def rename_old_new(df: FrameType) -> FrameType:
        """
        Renames the values in the 'old_new' column to descriptive labels:
        Y → New, N → Old.

        Args:
            df: Input frame with a column named 'old_new' of type String.
        Returns:
            Frame with old_new values replaced by their full names.
        """
        return df.with_columns(
            pl.col("old_new").replace({
                "Y": "New",
                "N": "Old",
            })
        )

    @staticmethod
    def sort_by_year_and_property_type(df: FrameType) -> FrameType:
        """
        Sorts the frame ascending by year then property_type.

        Args:
            df: Input frame with columns year and property_type.
        Returns:
            Frame sorted by year ascending, then property_type ascending.
        """
        return df.sort(["year", "property_type"])

    @staticmethod
    def summarise_by_year_and_property_type(df: FrameType) -> FrameType:
        """
        Summarises sales by year and property type, calculating total number of
        unique sales and max, min and median price per group.

        Args:
            df: Input frame with columns id, price, year, property_type.
        Returns:
            Frame grouped by year, property_type with columns
            total_sales, max_price, min_price, median_price.
        """
        return df.group_by(["year", "property_type"]).agg(
            pl.col("id").n_unique().alias("total_sales"),
            pl.col("price").max().alias("max_price"),
            pl.col("price").min().alias("min_price"),
            pl.col("price").median().alias("median_price"),
        )
