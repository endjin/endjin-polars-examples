@unit
Feature: Build a location dimension

  Scenario: Location dimension extracts unique location combinations
    Given the following price paid data exists
      | county:string       | district:string     | town_city:string | postcode_area:string |
      | GREATER LONDON      | WESTMINSTER         | LONDON           | SW1A                 |
      | GREATER LONDON      | WESTMINSTER         | LONDON           | SW1A                 |
      | GREATER MANCHESTER  | MANCHESTER          | MANCHESTER       | M1                   |
      | GREATER LONDON      | CAMDEN              | LONDON           | NW1                  |
    When I build the location dimension
    Then the location dimension should contain 3 unique rows
    And the location dimension should include the following locations
      | county:string       | district:string     | town_city:string | postcode_area:string |
      | GREATER LONDON      | CAMDEN              | LONDON           | NW1                  |
      | GREATER LONDON      | WESTMINSTER         | LONDON           | SW1A                 |
      | GREATER MANCHESTER  | MANCHESTER          | MANCHESTER       | M1                   |

  Scenario: Location dimension is sorted by county, district, town_city, postcode_area
    Given the following price paid data exists
      | county:string       | district:string     | town_city:string | postcode_area:string |
      | WEST YORKSHIRE      | LEEDS               | LEEDS            | LS1                  |
      | AVON                | BRISTOL             | BRISTOL          | BS1                  |
      | GREATER LONDON      | WESTMINSTER         | LONDON           | SW1A                 |
    When I build the location dimension
    Then the first location should be in county "AVON"
    And the last location should be in county "WEST YORKSHIRE"
