import os
import shutil
from behave import given, when, then
import polars as pl
from data_wrangler import DataWrangler, DeltaWriteMode


TEST_DATA_FOLDER = os.path.join(os.path.dirname(__file__), "..", "test_data")
TEST_OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), "..", "test_output")


class CapturingCsvDataSource:
    """
    A data source that captures written DataFrames for test inspection.
    Wraps LocalCsvDataSource behavior but intercepts write_to_table calls.
    """

    def __init__(self, data_folder: str, column_names: list[str]) -> None:
        self.data_folder = data_folder
        self.column_names = column_names
        self.written_tables: dict[str, pl.DataFrame] = {}

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
        # Capture the DataFrame for inspection
        key = f"{schema}.{table}"
        self.written_tables[key] = df

    def scan_table(self, schema: str, table: str) -> pl.LazyFrame:
        # Return the captured table as a LazyFrame
        key = f"{schema}.{table}"
        return self.written_tables[key].lazy()


@given('land registry CSV files exist in the test data folder')
def step_given_test_data_exists(context):
    csv_files = [f for f in os.listdir(TEST_DATA_FOLDER) if f.endswith(".csv")]
    assert csv_files, f"No CSV files found in {TEST_DATA_FOLDER}"
    context.test_data_folder = TEST_DATA_FOLDER
    # Clean up any previous test output to avoid schema mismatch
    if os.path.exists(TEST_OUTPUT_FOLDER):
        shutil.rmtree(TEST_OUTPUT_FOLDER)
    # Initialize capturing data source
    context.data_source = CapturingCsvDataSource(
        data_folder=TEST_DATA_FOLDER,
        column_names=DataWrangler.COLUMN_NAMES,
    )
    context.wrangler = DataWrangler(context.data_source)


@when('I run process_to_silver')
def step_when_run_process_to_silver(context):
    context.wrangler.process_to_silver()
    context.silver_table = context.data_source.written_tables.get("silver.price_paid_data")


@when('I run project_to_gold')
def step_when_run_project_to_gold(context):
    context.wrangler.project_to_gold()
    context.dim_date = context.data_source.written_tables.get("gold.dim_date")
    context.dim_location = context.data_source.written_tables.get("gold.dim_location")
    context.fact_price_paid = context.data_source.written_tables.get("gold.fact_price_paid")


@then('the silver table should be non-empty')
def step_then_silver_non_empty(context):
    assert context.silver_table is not None, "Silver table was not written"
    assert len(context.silver_table) > 0, "Silver table is empty"


@then('the silver table should contain the columns {columns}')
def step_then_silver_columns(context, columns):
    expected = [c.strip() for c in columns.split(",")]
    actual = context.silver_table.columns
    missing = [c for c in expected if c not in actual]
    assert not missing, f"Missing columns in silver table: {missing}"


@then('all property_type values should be from the renamed set {values}')
def step_then_property_type_values(context, values):
    allowed = {v.strip() for v in values.split(",")}
    actual = set(context.silver_table["property_type"].drop_nulls().to_list())
    unexpected = actual - allowed
    assert not unexpected, f"Unexpected property_type values: {unexpected}"


@then('all year values should be positive integers')
def step_then_year_positive(context):
    assert (context.silver_table["year"] > 0).all(), "Found non-positive year values"


@then('all price values should be positive integers')
def step_then_price_positive(context):
    assert (context.silver_table["price"] > 0).all(), "Found non-positive price values"


@then('the dim_date table should be non-empty')
def step_then_dim_date_non_empty(context):
    assert context.dim_date is not None, "dim_date table was not written"
    assert len(context.dim_date) > 0, "dim_date table is empty"


@then('the dim_location table should be non-empty')
def step_then_dim_location_non_empty(context):
    assert context.dim_location is not None, "dim_location table was not written"
    assert len(context.dim_location) > 0, "dim_location table is empty"


@then('the fact_price_paid table should be non-empty')
def step_then_fact_price_paid_non_empty(context):
    assert context.fact_price_paid is not None, "fact_price_paid table was not written"
    assert len(context.fact_price_paid) > 0, "fact_price_paid table is empty"


@then('dim_date should contain the columns {columns}')
def step_then_dim_date_columns(context, columns):
    expected = [c.strip() for c in columns.split(",")]
    actual = context.dim_date.columns
    missing = [c for c in expected if c not in actual]
    assert not missing, f"Missing columns in dim_date: {missing}"


@then('dim_location should contain the columns {columns}')
def step_then_dim_location_columns(context, columns):
    expected = [c.strip() for c in columns.split(",")]
    actual = context.dim_location.columns
    missing = [c for c in expected if c not in actual]
    assert not missing, f"Missing columns in dim_location: {missing}"


@then('fact_price_paid should contain the columns {columns}')
def step_then_fact_price_paid_columns(context, columns):
    expected = [c.strip() for c in columns.split(",")]
    actual = context.fact_price_paid.columns
    missing = [c for c in expected if c not in actual]
    assert not missing, f"Missing columns in fact_price_paid: {missing}"
