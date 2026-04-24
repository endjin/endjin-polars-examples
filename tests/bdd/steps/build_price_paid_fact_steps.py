from datetime import date

import polars as pl
from behave import given, when, then
from common_steps import behave_table_to_polars_dataframe
from data_wrangler import DataWrangler


@given('the following silver layer data exists')
def step_given_silver_data(context):
    context.df = behave_table_to_polars_dataframe(context.table)


@when('I build the price paid fact table')
def step_when_build_fact(context):
    context.result = DataWrangler.build_price_paid_fact(context.df)


@then('the fact table should contain {count:d} rows')
def step_then_fact_row_count(context, count):
    assert len(context.result) == count, f"Expected {count} rows, got {len(context.result)}"


@then('the fact table should have columns {columns}')
def step_then_fact_has_columns(context, columns):
    expected = [c.strip() for c in columns.split(",")]
    actual = context.result.columns
    missing = [c for c in expected if c not in actual]
    assert not missing, f"Missing columns: {missing}"


@then('the fact table should not have columns {columns}')
def step_then_fact_not_has_columns(context, columns):
    excluded = [c.strip() for c in columns.split(",")]
    actual = context.result.columns
    present = [c for c in excluded if c in actual]
    assert not present, f"Unexpected columns present: {present}"


@then('the date_of_transfer column should contain "{date_str}"')
def step_then_date_of_transfer(context, date_str):
    expected_date = date.fromisoformat(date_str)
    actual_date = context.result["date_of_transfer"][0]
    assert actual_date == expected_date, f"Expected {expected_date}, got {actual_date}"


@when('I build the price paid fact table with location dimension')
def step_when_build_fact_with_dimension(context):
    dim_location = DataWrangler.build_location_dimension(context.df)
    context.dim_location = dim_location
    context.result = DataWrangler.build_price_paid_fact(context.df, dim_location)


@then('the fact table should have a column "{column}"')
def step_then_fact_has_column(context, column):
    assert column in context.result.columns, f"Expected column '{column}' not found. Columns: {context.result.columns}"


@then('transactions in the same location should have the same location_id')
def step_then_same_location_same_id(context):
    # Group by location columns and check location_id is consistent
    grouped = context.result.group_by(["postcode_area", "town_city"]).agg(
        pl.col("location_id").n_unique().alias("unique_ids")
    )
    max_unique = grouped["unique_ids"].max()
    assert max_unique == 1, "Transactions in the same location have different location_ids"


@then('transactions in different locations should have different location_ids')
def step_then_different_locations_different_ids(context):
    # Get unique location_ids per location combination
    unique_locations = context.result.select(["postcode_area", "town_city", "location_id"]).unique()
    # Should have same number of rows as unique location_ids
    n_locations = len(unique_locations)
    n_unique_ids = unique_locations["location_id"].n_unique()
    assert n_locations == n_unique_ids, f"Expected {n_locations} unique location_ids, got {n_unique_ids}"
