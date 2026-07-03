from datetime import date

from behave import given, when, then
from common_steps import behave_table_to_polars_dataframe, compare_polars_dataframes
from data_wrangler import DataWrangler


@given("the daily date dimension start date is '{start_date}' and the end date is '{end_date}'")
def step_given_daily_date_range(context, start_date, end_date):
    context.start_date = date.fromisoformat(start_date)
    context.end_date = date.fromisoformat(end_date)


@when('I build the daily date dimension')
def step_when_build_daily_date_dimension(context):
    context.df = DataWrangler.build_daily_date_dimension(context.start_date, context.end_date)


@then('the daily date dimension should contain {count:d} rows')
def step_then_daily_date_dimension_row_count(context, count):
    actual_count = len(context.df)
    assert actual_count == count, f"Expected {count} rows but got {actual_count}"


@then('the daily date dimension should include the following data')
def step_then_daily_date_dimension(context):
    expected = behave_table_to_polars_dataframe(context.table)
    # Select only the columns specified in the expected table for comparison
    actual = context.df.select(expected.columns)
    compare_polars_dataframes(expected, actual)
