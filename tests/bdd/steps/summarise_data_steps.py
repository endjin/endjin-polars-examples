from behave import when
from data_wrangler import DataWrangler


@when('I summarise the data')
def step_when_summarise_data(context):
    context.df = DataWrangler.summarise_data(context.df)
