from behave import when
from data_wrangler import summarise_data


@when('I summarise the data')
def step_when_summarise_data(context):
    context.df = summarise_data(context.df)
