from behave import when
from data_wrangler import rename_property_type


@when('I rename property types')
def step_when_rename_property_types(context):
    context.df = rename_property_type(context.df)
