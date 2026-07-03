from behave import when
from data_wrangler import DataWrangler


@when('I extract the postcode area from the full postcode')
def step_when_extract_postcode_area(context):
    context.df = DataWrangler.extract_postcode_area(context.df)
