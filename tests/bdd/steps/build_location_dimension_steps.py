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
    # Sort both for comparison
    result_sorted = context.result.sort(["county", "district", "town_city", "postcode_area"])
    expected_sorted = expected.sort(["county", "district", "town_city", "postcode_area"])
    
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
