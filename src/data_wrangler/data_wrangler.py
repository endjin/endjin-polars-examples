import polars as pl
from datetime import date

FrameType = pl.DataFrame | pl.LazyFrame


class DataWrangler:

    COLUMN_NAMES = [
        "id", "price", "date", "postcode", "property_type",
        "old_new", "duration", "paon", "saon", "street",
        "locality", "town_city", "district", "county",
        "ppd_category", "record_type",
    ]

    @staticmethod
    def load_data(data_folder: str) -> pl.LazyFrame:
        """
        Scans all pp-*.csv files in data_folder as a lazy frame, naming columns
        per the Land Registry positional schema and casting price/date to their
        native types.
        """
        return (
            pl.scan_csv(
                f"{data_folder}/pp-*.csv",
                has_header=False,
                new_columns=DataWrangler.COLUMN_NAMES,
                infer_schema_length=0,
                null_values=[""],
            )
            .with_columns(
                pl.col("price").cast(pl.Int64),
                pl.col("date").str.to_date(format="%Y-%m-%d %H:%M"),
            )
        )

    @classmethod
    def run_pipeline(cls, data_folder: str) -> pl.DataFrame:
        """
        Loads all CSVs from data_folder and runs the full transformation and
        summarisation pipeline, returning an eager summary DataFrame.
        """
        return (
            cls.load_data(data_folder)
            .pipe(cls.drop_records_without_postcode)
            .pipe(cls.drop_records_without_date)
            .pipe(cls.filter_other_property_types)
            .pipe(cls.extract_year_from_date)
            .pipe(cls.rename_property_type)
            .pipe(cls.rename_duration)
            .pipe(cls.rename_old_new)
            .pipe(cls.extract_postcode_area)
            .pipe(cls.summarise_by_year_and_property_type)
            .pipe(cls.sort_by_year_and_property_type)
            .collect()  # type: ignore[union-attr]
        )

    @staticmethod
    def filter_other_property_types(df: FrameType) -> FrameType:
        """
        Filters the DataFrame to include only rows where property_type is not 'Other'.

        Args:
            df: Input frame with a column named 'property_type'.
        Returns:
            Frame containing only rows where property_type is not 'O'.
        """
        return df.filter(pl.col("property_type") != "O")

    @staticmethod
    def extract_year_from_date(df: FrameType) -> FrameType:
        """
        Extracts the year from the 'date' column and adds it as a new column 'year'.

        Args:
            df: Input frame with a column named 'date' of type Date.
        Returns:
            Frame with an additional integer column 'year'.
        """
        return df.with_columns(
            pl.col("date").dt.year().alias("year"),
        )

    @staticmethod
    def build_date_dimension_table(start_date: date, end_date: date) -> pl.DataFrame:
        """
        Builds a date dimension table for the inclusive range [start_date, end_date].

        Args:
            start_date: First date in the range.
            end_date: Last date in the range (inclusive).
        Returns:
            DataFrame with one row per date and columns: date, year, month, month_name,
            day, day_name, weekday, is_weekend, is_leap_year.
        """
        date_range = pl.date_range(start_date, end_date, interval="1d", eager=True)
        return (
            pl.DataFrame({"date": date_range})
            .with_columns(
                pl.col("date").dt.year().alias("year"),
                pl.col("date").dt.month().alias("month"),
                pl.col("date").dt.day().alias("day"),
                pl.col("date").dt.weekday().alias("weekday"),
                pl.col("date").dt.is_leap_year().alias("is_leap_year"),
                pl.col("date").dt.to_string("%B").alias("month_name"),
                pl.col("date").dt.to_string("%A").alias("day_name"),
                (pl.col("date").dt.weekday() >= 6).alias("is_weekend"),
            )
        )

    @staticmethod
    def extract_postcode_area(df: FrameType) -> FrameType:
        """
        Extracts the postcode area (outward code) from the 'postcode' column using
        strict UK postcode validation. Returns null for any postcode that does not
        match the standard format.

        Args:
            df: Input frame with a column named 'postcode' of type String.
        Returns:
            Frame with an additional column 'postcode_area' (e.g. 'SW1A' from 'SW1A 2AA').
        """
        return df.with_columns(
            pl.col("postcode")
            .str.extract(r"^([A-Z]{1,2}[0-9R][0-9A-Z]?) [0-9][ABD-HJLNP-UW-Z]{2}$", 1)
            .alias("postcode_area")
        )

    @staticmethod
    def extract_postcode_district(df: FrameType) -> FrameType:
        """
        Extracts the postcode district from the 'postcode' column and adds it as a
        new column 'postcode_district' (e.g. 'SW1' from 'SW1A 2AA').

        Args:
            df: Input frame with a column named 'postcode' of type String.
        Returns:
            Frame with an additional column 'postcode_district'.
        """
        return df.with_columns(
            pl.col("postcode").str.extract(r"^([A-Z]{1,2}[0-9R][0-9A-Z]?)\s", 1).alias("postcode_district")
        )

    @staticmethod
    def drop_records_without_postcode(df: FrameType) -> FrameType:
        """
        Drops records where the 'postcode' column is null or empty.

        Args:
            df: Input frame with a column named 'postcode' of type String.
        Returns:
            Frame with only rows where postcode is present and non-empty.
        """
        return df.filter(pl.col("postcode").is_not_null() & (pl.col("postcode") != ""))

    @staticmethod
    def drop_records_without_date(df: FrameType) -> FrameType:
        """
        Drops records where the 'date' column is null.

        Args:
            df: Input frame with a column named 'date' of type Date.
        Returns:
            Frame with only rows where date is present.
        """
        return df.filter(pl.col("date").is_not_null())

    @staticmethod
    def rename_property_type(df: FrameType) -> FrameType:
        """
        Renames the values in the 'property_type' column to descriptive labels:
        D → Detached, S → Semi-Detached, T → Terraced, F → Flat, O → Other.

        Args:
            df: Input frame with a column named 'property_type' of type String.
        Returns:
            Frame with property_type values replaced by their full names.
        """
        return df.with_columns(
            pl.col("property_type").replace({
                "D": "Detached",
                "S": "Semi-Detached",
                "T": "Terraced",
                "F": "Flat",
                "O": "Other",
            })
        )

    @staticmethod
    def rename_duration(df: FrameType) -> FrameType:
        """
        Renames the values in the 'duration' column to descriptive labels:
        F → Freehold, L → Leasehold, U → Unknown.

        Args:
            df: Input frame with a column named 'duration' of type String.
        Returns:
            Frame with duration values replaced by their full names.
        """
        return df.with_columns(
            pl.col("duration").replace({
                "F": "Freehold",
                "L": "Leasehold",
                "U": "Unknown",
            })
        )

    @staticmethod
    def rename_old_new(df: FrameType) -> FrameType:
        """
        Renames the values in the 'old_new' column to descriptive labels:
        Y → New, N → Old.

        Args:
            df: Input frame with a column named 'old_new' of type String.
        Returns:
            Frame with old_new values replaced by their full names.
        """
        return df.with_columns(
            pl.col("old_new").replace({
                "Y": "New",
                "N": "Old",
            })
        )

    @staticmethod
    def sort_by_year_and_property_type(df: FrameType) -> FrameType:
        """
        Sorts the frame ascending by year then property_type.

        Args:
            df: Input frame with columns year and property_type.
        Returns:
            Frame sorted by year ascending, then property_type ascending.
        """
        return df.sort(["year", "property_type"])

    @staticmethod
    def summarise_by_year_and_property_type(df: FrameType) -> FrameType:
        """
        Summarises sales by year and property type, calculating total number of
        unique sales and max, min and median price per group.

        Args:
            df: Input frame with columns id, price, year, property_type.
        Returns:
            Frame grouped by year, property_type with columns
            total_sales, max_price, min_price, median_price.
        """
        return df.group_by(["year", "property_type"]).agg(
            pl.col("id").n_unique().alias("total_sales"),
            pl.col("price").max().alias("max_price"),
            pl.col("price").min().alias("min_price"),
            pl.col("price").median().alias("median_price"),
        )
