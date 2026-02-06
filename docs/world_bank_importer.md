# World Bank Data Importer

This document details the implementation of the `WorldBankDataImporter` class, which fetches data from the World Bank's Data360 API and metadata from the V2 API.

## API Reference

*   **Official Documentation**: [World Bank Data360 API](https://data360.worldbank.org/en/api)
*   **Data Endpoint**: `https://data360api.worldbank.org/data360/data`
*   **Metadata Endpoint**: `https://data360api.worldbank.org/data360/metadata`
*   **Legacy V2 Endpoint (for Countries)**: `https://api.worldbank.org/v2/country`

## Design Decisions

### 1. Hybrid API Approach
The implementation uses a hybrid approach to leverage the strengths of different World Bank API versions:

*   **Data360 API**: Used for fetching indicator data and indicator metadata. It supports bulk fetching (multiple indicators/countries in one request) and OData-style filtering, which significantly improves performance and simplicity.
*   **V2 API**: Used for fetching the list of countries (`get_countries`). The V2 API provides a rich, standardized list of countries with metadata (region, income level, coordinates) that is well-structured for this specific purpose.

### 2. Indicator Code Formatting
The Data360 API uses a specific naming convention for indicators, typically prefixing them with the database ID (e.g., `WB_WDI_`) and replacing dots with underscores.

*   **User Input**: Users can provide standard World Bank codes (e.g., `SP.POP.TOTL`).
*   **Internal Handling**: The class automatically detects if the prefix is missing and converts `SP.POP.TOTL` to `WB_WDI_SP_POP_TOTL`. This maintains backward compatibility with common usage patterns while satisfying the API's requirements.

### 3. Pagination Strategy
The API uses a `skip` parameter for pagination and returns a `count` of total records.

*   **Implementation**: A `while` loop continues to fetch data, incrementing the `skip` parameter by the number of items returned in the current page, until the number of fetched items equals the total `count`.
*   **Page Size**: We rely on the API's default page size (or implicit max) but handle whatever chunk size the API returns.

### 4. Data Structure
The data is returned as a **Polars DataFrame** in "long" format.

**Data Schema (`get_data`):**
*   `country_code` (String): ISO3 country code (e.g., 'USA', 'GBR').
*   `year` (Int64): The year of the observation.
*   `indicator_code` (String): The indicator code (e.g., 'WB_WDI_SP_POP_TOTL').
*   `value` (Float64): The numerical value of the indicator.

**Metadata Schema (`get_indicator_metadata`):**
*   `name` (String): The indicator ID (e.g., 'WB_WDI_SP_POP_TOTL').
*   `description` (String): The human-readable name (e.g., 'Population, total').
*   `aggregation_method` (String): How the data is aggregated (e.g., 'Sum').
*   `definition_long` (String): Detailed definition.
*   `statistical_concept` (String): Explanation of the statistical concept.
*   `methodology` (String): How the data is collected/calculated.
*   `limitation` (String): Known limitations of the data.
*   `relevance` (String): Why the indicator is relevant.

This format was chosen because it is the most flexible for downstream analysis. Users can easily `pivot` the DataFrame if they want indicators as columns.

### 5. Error Handling
*   **Retries**: The implementation includes basic retry logic (via `requests` or custom loops in previous iterations) to handle transient network issues.
*   **Logging**: The class uses Python's `logging` module to provide visibility into the fetching process (e.g., current page, errors) without cluttering stdout with print statements.
