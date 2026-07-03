import polars as pl
from behave import given, when, then
from common_steps import behave_table_to_polars_dataframe
from data_wrangler import price_paid_data_schema


@given('the following valid price paid data row exists')
def step_given_valid_row(context):
    context.df = behave_table_to_polars_dataframe(context.table)


@given('the {field} is null')
def step_given_field_is_null(context, field):
    dtype = context.df[field].dtype
    context.df = context.df.with_columns(pl.lit(None).cast(dtype).alias(field))


@given('the price is {value:d}')
def step_given_price_is(context, value):
    context.df = context.df.with_columns(pl.lit(value, dtype=pl.Int64).alias("price"))


@given('the {field} is "{value}"')
def step_given_field_is_string(context, field, value):
    context.df = context.df.with_columns(pl.lit(value).alias(field))


@when('I validate the price paid data')
def step_when_validate(context):
    try:
        context.validated_df = price_paid_data_schema.validate(context.df)
        context.validation_error = None
    except Exception as e:
        context.validated_df = None
        context.validation_error = e


@then('the validation should pass without errors')
def step_then_pass(context):
    assert context.validation_error is None, f"Expected no error but got: {context.validation_error}"


@then('the validation should fail with appropriate error messages')
def step_then_fail(context):
    assert context.validation_error is not None, "Expected validation to fail but it passed"
