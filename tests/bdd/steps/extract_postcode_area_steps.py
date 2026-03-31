from behave import when
from data_wrangler import extract_postcode_area


@when('I extract the postcode area from the full postcode')
def step_when_extract_postcode_area(context):
    context.df = extract_postcode_area(context.df)
