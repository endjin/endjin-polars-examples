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


@when('I build the price paid fact table with location dimension')
def step_when_build_fact_with_dimension(context):
    dim_location = DataWrangler.build_location_dimension(context.df)
    context.dim_location = dim_location
    context.result = DataWrangler.build_price_paid_fact(context.df, dim_location)


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


@then('the fact table should have a column "{column}"')
def step_then_fact_has_column(context, column):
    assert column in context.result.columns, f"Expected column '{column}' not found. Columns: {context.result.columns}"


@then('the aggregated row should have min_price {min_price:d}, median_price {median_price:d}, max_price {max_price:d}, transaction_count {count:d}')
def step_then_aggregated_prices(context, min_price, median_price, max_price, count):
    row = context.result.row(0, named=True)
    assert row["min_price"] == min_price, f"Expected min_price {min_price}, got {row['min_price']}"
    assert row["median_price"] == float(median_price), f"Expected median_price {median_price}, got {row['median_price']}"
    assert row["max_price"] == max_price, f"Expected max_price {max_price}, got {row['max_price']}"
    assert row["transaction_count"] == count, f"Expected transaction_count {count}, got {row['transaction_count']}"
