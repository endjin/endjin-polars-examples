@e2e
Feature: Run data wrangler pipeline end-to-end

  Scenario: Load, transform and clean Land Registry data from CSV files
    Given land registry CSV files exist in the test data folder
    When I run the pipeline
    Then the result should be a non-empty DataFrame
    And the result should contain the columns price, date, postcode, property_type, year, postcode_area
    And all property_type values should be from the renamed set Detached, Semi-Detached, Terraced, Flat
    And all year values should be positive integers
    And all price values should be positive integers
