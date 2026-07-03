from pandera.polars import DataFrameSchema, Column, Check
import polars as pl


price_paid_data_schema = DataFrameSchema(
    {
        "id": Column(pl.String, nullable=False),
        "price": Column(pl.Int64, checks=Check.greater_than(0), nullable=False),
        "date": Column(pl.Date, nullable=False),
        "postcode": Column(pl.String, nullable=True),
        "property_type": Column(pl.String, checks=Check.isin(["D", "S", "T", "F", "O"]), nullable=False),
        "old_new": Column(pl.String, checks=Check.isin(["Y", "N"]), nullable=False),
        "duration": Column(pl.String, nullable=False),
        "paon": Column(pl.String, nullable=True),
        "saon": Column(pl.String, nullable=True),
        "street": Column(pl.String, nullable=True),
        "locality": Column(pl.String, nullable=True),
        "town_city": Column(pl.String, nullable=True),
        "district": Column(pl.String, nullable=True),
        "county": Column(pl.String, nullable=True),
        "ppd_category": Column(pl.String, checks=Check.isin(["A", "B"]), nullable=False),
        "record_type": Column(pl.String, checks=Check.isin(["A", "C", "D"]), nullable=False),
    }
)
