from behave import when
from data_wrangler import drop_records_without_postcode


@when('I drop rows with no postcode')
def step_when_drop_rows_with_no_postcode(context):
    context.df = drop_records_without_postcode(context.df)
