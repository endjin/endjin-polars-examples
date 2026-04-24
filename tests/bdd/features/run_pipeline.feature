@e2e
Feature: Run data wrangler pipeline end-to-end

  Scenario: Process raw Land Registry data to silver layer
    Given land registry CSV files exist in the test data folder
    When I run process_to_silver
    Then the silver table should be non-empty
    And the silver table should contain the columns price, date, postcode, property_type, year, postcode_area
    And all property_type values should be from the renamed set Detached, Semi-Detached, Terraced, Flat
    And all year values should be positive integers
    And all price values should be positive integers

  Scenario: Project silver data to gold layer dimensional model
    Given land registry CSV files exist in the test data folder
    When I run process_to_silver
    And I run project_to_gold
    Then the dim_date table should be non-empty
    And the dim_location table should be non-empty
    And the fact_price_paid table should be non-empty
    And dim_date should contain the columns date, year, month, month_name, day_name, is_weekend
    And dim_location should contain the columns county, district, town_city, postcode_area
    And fact_price_paid should contain the columns price, date_of_transfer, postcode, property_type
