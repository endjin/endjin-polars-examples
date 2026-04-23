from datetime import date
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
