from behave import when
from data_wrangler import rename_duration


@when('I rename durations')
def step_when_rename_durations(context):
    context.df = rename_duration(context.df)
