import polars as pl
from datetime import date

def validate_price_paid_data(df: pl.DataFrame) -> pl.DataFrame:
    """
    Validates the input DataFrame against the defined schema for price paid data.

    Args:
        df: The input Polars DataFrame to validate.
    Returns:
        The validated Polars DataFrame if it conforms to the schema.
    Raises:
        pandera.errors.SchemaError: If the DataFrame does not conform to the schema.
    """
    from .schema_price_paid_data import price_paid_data_schema
    return price_paid_data_schema.validate(df)


def filter_other_property_types(df: pl.DataFrame) -> pl.DataFrame:
    """
    Filters the DataFrame to include only rows where 'PropertyType' is not 'Other'.

    Args:
        df: The input Polars DataFrame. It is expected to have a column named 'PropertyType'.
    Returns:
        A Polars DataFrame containing only rows where 'PropertyType' is not 'Other'.
    """
    return df.filter(pl.col("property_type") != "O")

def extract_year_from_date(df: pl.DataFrame) -> pl.DataFrame:
    """
    Extracts the year and month from the 'Date' column and adds them as new columns 'YearOfSale' and 'MonthOfSale'.

    Args:
        df: The input Polars DataFrame. It is expected to have a column named 'Date' of type Date.
    Returns:
        A Polars DataFrame with new columns 'YearOfSale' and 'MonthOfSale' extracted from the 'Date' column.
    """
    return df.with_columns(
        pl.col("Date").dt.year().alias("YearOfSale"),
    )
    
def build_date_dimension_table(start_date: date, end_date: date) -> pl.DataFrame:
    """
    Builds a date dimension table based on the start_date and end_date inclusive.

    Args:
        start_date: The start date for the date dimension table.
        end_date: The end date for the date dimension table.
    Returns:
        A Polars DataFrame representing the date dimension table with unique dates and their components.
        Includes:
        - date: The unique date.
        - year: The year component of the date.
        - month: The month number component of the date.
        - month_name: The month name component of the date.
        - day: The day component of the date.
        - day_name: The day name component of the date.
        - weekday: The weekday component of the date (0=Monday, 6=Sunday).
        - is_weekend: A boolean indicating whether the date is a weekend.
        - is_leap_year: A boolean indicating whether the year is a leap year.
    """
    date_range = pl.date_range(start_date, end_date, interval="1d", eager=True)
    date_dim_df = pl.DataFrame({"date": date_range})
    date_dim_df = date_dim_df.with_columns(
        pl.col("date").dt.year().alias("year"),
        pl.col("date").dt.month().alias("month"),
        pl.col("date").dt.day().alias("day"),
        pl.col("date").dt.weekday().alias("weekday"),
        pl.col("date").dt.is_leap_year().alias("is_leap_year"),
        pl.col("date").dt.to_string("%B").alias("month_name"),
        pl.col("date").dt.to_string("%A").alias("day_name"),
        (pl.col("date").dt.weekday() >= 6).alias("is_weekend")
    )
    return date_dim_df

def extract_postcode_area(df: pl.DataFrame) -> pl.DataFrame:
    """
    Extracts the postcode area from the 'postcode' column and adds it as a new column 'postcode_area'.
    Uses regex expression to extract the area part of the postcode, which is typically the first two letters before the first space in the postcode.
        df: The input Polars DataFrame. It is expected to have a column named 'postcode' of type String.
    Returns:
        A Polars DataFrame with a new column 'postcode_area' extracted from the 'postcode' column.
    """
    return df.with_columns(
        pl.col("postcode").str.extract(r"^([A-Z]{1,2})\d", 1).alias("postcode_area")
    )
    
def drop_records_without_postcode(df: pl.DataFrame) -> pl.DataFrame:
    """
    Drops records from the DataFrame where the 'postcode' column is null or empty.

    Args:
        df: The input Polars DataFrame. It is expected to have a column named 'postcode' of type String.
    Returns:
        A Polars DataFrame with records where the 'postcode' column is not null or empty.
    """
    return df.filter(pl.col("postcode").is_not_null() & (pl.col("postcode") != ""))

def drop_records_without_date(df: pl.DataFrame) -> pl.DataFrame:
    """
    Drops records from the DataFrame where the 'date' column is null.

    Args:
        df: The input Polars DataFrame. It is expected to have a column named 'date' of type Date.
    Returns:
        A Polars DataFrame with records where the 'date' column is not null.
    """
    return df.filter(pl.col("date").is_not_null())

def rename_property_type(df: pl.DataFrame) -> pl.DataFrame:
    """
    Renames the values in the 'property_type' column to more descriptive names.

    Args:
        df: The input Polars DataFrame. It is expected to have a column named 'property_type' of type String.
    Returns:
        A Polars DataFrame with the 'property_type' column values renamed to more descriptive names:
        - 'D' to 'Detached'
        - 'S' to 'Semi-Detached'
        - 'T' to 'Terraced'
        - 'F' to 'Flat'
        - 'O' to 'Other'
    """
    return df.with_columns(
        pl.col("property_type").map_dict({
            "D": "Detached",
            "S": "Semi-Detached",
            "T": "Terraced",
            "F": "Flat",
            "O": "Other"
        }).alias("property_type")
    )
    
def rename_duration(df: pl.DataFrame) -> pl.DataFrame:
    """
    Renames the values in the 'duration' column to more descriptive names.

    Args:
        df: The input Polars DataFrame. It is expected to have a column named 'duration' of type String.
    Returns:
        A Polars DataFrame with the 'duration' column values renamed to more descriptive names:
        - 'F' to 'Freehold'
        - 'L' to 'Leasehold'
        - 'U' to 'Unknown'
    """
    return df.with_columns(
        pl.col("duration").map_dict({
            "F": "Freehold",
            "L": "Leasehold",
            "U": "Unknown"
        }).alias("duration")
    )   
    
def rename_old_new(df: pl.DataFrame) -> pl.DataFrame:
    """
    Renames the values in the 'old_new' column to more descriptive names.

    Args:
        df: The input Polars DataFrame. It is expected to have a column named 'old_new' of type String.
    Returns:
        A Polars DataFrame with the 'old_new' column values renamed to more descriptive names:
        - 'Y' to 'New'
        - 'N' to 'Old'
    """
    return df.with_columns(
        pl.col("old_new").map_dict({
            "Y": "New",
            "N": "Old"
        }).alias("old_new")
    )
    
def summarise_data(df: pl.DataFrame) -> pl.DataFrame:
    """
    Summarises the data by
    - year
    - property type
    - town_city
    - county
    
    Calculating:
    - the total number of sales by counting unique 'id' values
    - the max, min and median price from the price_paid column

    Args:
        df: The input Polars DataFrame.
    Returns:
        A Polars DataFrame summarised by year, property type, town_city and county with the total number of sales and the max, min and median price.
    """
    return df.group_by(["YearOfSale", "property_type", "town_city", "county"]).agg(
        pl.col("id").n_unique().alias("total_sales"),
        pl.col("price").max().alias("max_price"),
        pl.col("price").min().alias("min_price"),
        pl.col("price").median().alias("median_price")
    )