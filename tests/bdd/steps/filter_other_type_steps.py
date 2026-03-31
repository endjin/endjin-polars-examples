from behave import given, when, then
from common_steps import behave_table_to_polars_dataframe, compare_polars_dataframes
from data_wrangler import filter_other_property_types


@given('a dataset with the following rows')
def step_given_dataset(context):
    context.df = behave_table_to_polars_dataframe(context.table)


@when('I filter out rows where property_type is other')
def step_when_filter_other(context):
    context.df = filter_other_property_types(context.df)


@then('the resulting dataset should include the following rows')
def step_then_resulting_dataset(context):
    expected = behave_table_to_polars_dataframe(context.table)
    compare_polars_dataframes(expected, context.df)
