from behave import when
from data_wrangler import DataWrangler


@when('I rename durations')
def step_when_rename_durations(context):
    context.df = DataWrangler.rename_duration(context.df)
