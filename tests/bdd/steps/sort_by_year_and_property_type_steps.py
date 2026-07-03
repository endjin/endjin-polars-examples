import polars.testing as pl_testing
from behave import when, then
from common_steps import behave_table_to_polars_dataframe
from data_wrangler import DataWrangler


@when('I sort by year and property type')
def step_when_sort_by_year_and_property_type(context):
    context.df = DataWrangler.sort_by_year_and_property_type(context.df)


@then('the resulting dataset should be in the following order')
def step_then_ordered(context):
    expected = behave_table_to_polars_dataframe(context.table)
    cols = expected.columns
    pl_testing.assert_frame_equal(expected, context.df.select(cols), check_dtypes=False)
