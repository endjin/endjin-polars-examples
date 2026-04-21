from datetime import date

import polars as pl
import polars.testing as pl_testing

from data_wrangler import DataWrangler


class FakePricePaidDataSource:
    def scan_price_paid(self) -> pl.LazyFrame:
        return pl.DataFrame(
            {
                "id": ["1", "2", "3"],
                "price": [250000, 300000, 125000],
                "date": [date(2024, 1, 2), date(2024, 2, 5), date(2024, 3, 8)],
                "postcode": ["SW1A 2AA", "M1 1AE", "BS1 5AH"],
                "property_type": ["D", "S", "O"],
                "duration": ["F", "L", "F"],
                "old_new": ["N", "Y", "N"],
            }
        ).lazy()


def test_run_pipeline_with_data_source_injection() -> None:
    result = DataWrangler.run_pipeline_with_data_source(FakePricePaidDataSource())

    expected = pl.DataFrame(
        {
            "year": [2024, 2024],
            "property_type": ["Detached", "Semi-Detached"],
            "total_sales": [1, 1],
            "max_price": [250000, 300000],
            "min_price": [250000, 300000],
            "median_price": [250000.0, 300000.0],
        }
    )

    sort_cols = ["year", "property_type"]
    pl_testing.assert_frame_equal(
        result.select(expected.columns).sort(sort_cols),
        expected.sort(sort_cols),
        check_dtypes=False,
    )
