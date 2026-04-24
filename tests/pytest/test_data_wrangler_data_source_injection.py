from datetime import date

import polars as pl
import polars.testing as pl_testing

from data_wrangler import DataWrangler, DeltaWriteMode


class FakePricePaidDataSource:
    def __init__(self) -> None:
        self.written_tables: dict[str, pl.DataFrame] = {}
        self.written_schemas: dict[str, str] = {}
        self.written_modes: dict[str, str] = {}

    def scan_price_paid(self) -> pl.LazyFrame:
        return pl.DataFrame(
            {
                "id": ["1", "2", "3"],
                "price": [250000, 300000, 125000],
                "date": [date(2024, 1, 2), date(2024, 2, 5), date(2024, 3, 8)],
                "postcode": ["SW1A 2AA", "M1 1AE", "BS1 5AH"],
                "property_type": ["D", "S", "O"],
                "duration": ["F", "L", "F"],
                "old_new": ["N", "Y", "N"],
                "county": ["GREATER LONDON", "GREATER MANCHESTER", "AVON"],
                "district": ["WESTMINSTER", "MANCHESTER", "BRISTOL"],
                "town_city": ["LONDON", "MANCHESTER", "BRISTOL"],
            }
        ).lazy()

    def write_to_table(
        self,
        df: pl.DataFrame,
        schema: str,
        table: str,
        mode: DeltaWriteMode = "overwrite",
    ) -> None:
        self.written_tables[table] = df
        self.written_schemas[table] = schema
        self.written_modes[table] = mode

    def scan_table(self, schema: str, table: str) -> pl.LazyFrame:
        """Return the written table as a LazyFrame for reading."""
        return self.written_tables[table].lazy()


def test_process_to_silver() -> None:
    """Test that process_to_silver produces full-fidelity cleaned data."""
    data_source = FakePricePaidDataSource()
    DataWrangler.run_pipeline_with_data_source(data_source)

    # Inspect the silver table that was written
    silver_data = data_source.written_tables["price_paid_data"]

    # Should have 2 rows (O/Other is filtered out)
    assert len(silver_data) == 2

    # Should have renamed property types
    assert set(silver_data["property_type"].to_list()) == {"Detached", "Semi-Detached"}

    # Should have year extracted
    assert "year" in silver_data.columns
    assert silver_data["year"].to_list() == [2024, 2024]

    # Should have postcode_area extracted
    assert "postcode_area" in silver_data.columns

    # Verify write was called with correct parameters
    assert data_source.written_schemas["price_paid_data"] == "silver"
    assert data_source.written_modes["price_paid_data"] == "overwrite"


def test_project_to_gold() -> None:
    """Test that project_to_gold creates dimensional model from silver table."""
    data_source = FakePricePaidDataSource()
    DataWrangler.run_pipeline_with_data_source(data_source)

    # Verify all three gold tables were written
    assert "dim_date" in data_source.written_tables
    assert "dim_location" in data_source.written_tables
    assert "fact_price_paid" in data_source.written_tables

    # Verify dim_date has expected columns (monthly granularity)
    dim_date = data_source.written_tables["dim_date"]
    assert "year_month" in dim_date.columns
    assert "year" in dim_date.columns
    assert "quarter" in dim_date.columns
    assert "month" in dim_date.columns
    assert "month_name" in dim_date.columns

    # Verify dim_location has expected columns
    dim_location = data_source.written_tables["dim_location"]
    assert "location_id" in dim_location.columns
    assert "county" in dim_location.columns
    assert "district" in dim_location.columns
    assert "postcode_area" in dim_location.columns

    # Verify fact_price_paid has expected columns (aggregated)
    fact = data_source.written_tables["fact_price_paid"]
    assert "location_id" in fact.columns
    assert "year_month" in fact.columns
    assert "property_type" in fact.columns
    assert "min_price" in fact.columns
    assert "median_price" in fact.columns
    assert "max_price" in fact.columns
    assert "transaction_count" in fact.columns

    # Verify all tables written to gold schema
    assert data_source.written_schemas["dim_date"] == "gold"
    assert data_source.written_schemas["dim_location"] == "gold"
    assert data_source.written_schemas["fact_price_paid"] == "gold"
