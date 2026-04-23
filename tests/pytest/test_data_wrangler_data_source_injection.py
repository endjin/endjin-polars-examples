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


def test_process_to_silver() -> None:
    """Test that process_to_silver produces full-fidelity cleaned data."""
    data_source = FakePricePaidDataSource()
    result = DataWrangler.run_pipeline_with_data_source(data_source)

    # Should have 2 rows (O/Other is filtered out)
    assert len(result) == 2

    # Should have renamed property types
    assert set(result["property_type"].to_list()) == {"Detached", "Semi-Detached"}

    # Should have year extracted
    assert "year" in result.columns
    assert result["year"].to_list() == [2024, 2024]

    # Should have postcode_area extracted
    assert "postcode_area" in result.columns

    # Verify write was called with correct parameters
    assert data_source.written_schemas["price_paid_data"] == "silver"
    assert data_source.written_modes["price_paid_data"] == "overwrite"


def test_process_to_gold() -> None:
    """Test that process_to_gold creates dimensional model."""
    data_source = FakePricePaidDataSource()
    wrangler = DataWrangler(data_source)

    # First process to silver
    silver_data = wrangler.process_to_silver()

    # Then process to gold
    gold_tables = wrangler.process_to_gold(silver_data)

    # Verify all three tables are created
    assert "dim_date" in gold_tables
    assert "dim_location" in gold_tables
    assert "fact_price_paid" in gold_tables

    # Verify dim_date has expected columns
    dim_date = gold_tables["dim_date"]
    assert "date" in dim_date.columns
    assert "year" in dim_date.columns
    assert "month_name" in dim_date.columns
    assert "day_name" in dim_date.columns

    # Verify dim_location has expected columns
    dim_location = gold_tables["dim_location"]
    assert "county" in dim_location.columns
    assert "district" in dim_location.columns
    assert "postcode_area" in dim_location.columns

    # Verify fact_price_paid has expected columns
    fact = gold_tables["fact_price_paid"]
    assert "price" in fact.columns
    assert "date_of_transfer" in fact.columns
    assert "postcode_area" in fact.columns

    # Verify all tables written to gold schema
    assert data_source.written_schemas["dim_date"] == "gold"
    assert data_source.written_schemas["dim_location"] == "gold"
    assert data_source.written_schemas["fact_price_paid"] == "gold"
