import polars as pl
from behave import given, when, then
from common_steps import behave_table_to_polars_dataframe
from data_wrangler import DataWrangler


@given('the following price paid data exists')
def step_given_price_paid_data(context):
    context.df = behave_table_to_polars_dataframe(context.table)


@when('I build the location dimension')
def step_when_build_location_dimension(context):
    context.result = DataWrangler.build_location_dimension(context.df)


@then('the location dimension should contain {count:d} unique rows')
def step_then_location_count(context, count):
    assert len(context.result) == count, f"Expected {count} rows, got {len(context.result)}"


@then('the location dimension should include the following locations')
def step_then_location_includes(context):
    expected = behave_table_to_polars_dataframe(context.table)
    # Compare only the columns from expected (excluding location_id)
    compare_cols = expected.columns
    result_sorted = context.result.select(compare_cols).sort(compare_cols)
    expected_sorted = expected.sort(compare_cols)
    
    assert result_sorted.equals(expected_sorted), (
        f"Location dimension mismatch.\nExpected:\n{expected_sorted}\nGot:\n{result_sorted}"
    )


@then('the first location should be in county "{county}"')
def step_then_first_county(context, county):
    first_county = context.result["county"][0]
    assert first_county == county, f"Expected first county '{county}', got '{first_county}'"


@then('the last location should be in county "{county}"')
def step_then_last_county(context, county):
    last_county = context.result["county"][-1]
    assert last_county == county, f"Expected last county '{county}', got '{last_county}'"


@then('the location dimension should have a column "{column}"')
def step_then_has_column(context, column):
    assert column in context.result.columns, f"Expected column '{column}' not found. Columns: {context.result.columns}"


@then('the location_id values should be unique')
def step_then_location_id_unique(context):
    location_ids = context.result["location_id"].to_list()
    assert len(location_ids) == len(set(location_ids)), "location_id values are not unique"


@then('the location_id values should start from {start:d}')
def step_then_location_id_starts_from(context, start):
    min_id = context.result["location_id"].min()
    assert min_id == start, f"Expected location_id to start from {start}, got {min_id}"
