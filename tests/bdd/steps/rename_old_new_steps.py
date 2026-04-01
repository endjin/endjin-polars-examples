from behave import when
from data_wrangler import rename_old_new


@when('I rename old_new values')
def step_when_rename_old_new(context):
    context.df = rename_old_new(context.df)
