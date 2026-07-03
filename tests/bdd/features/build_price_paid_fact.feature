@unit
Feature: Build a price paid fact table

  Scenario: Fact table aggregates prices by month and location
    Given the following silver layer data exists
      | id:string | price:integer | date:date  | postcode:string | postcode_area:string | property_type:string | old_new:string | duration:string | county:string  | district:string | town_city:string |
      | 1         | 250000        | 2024-01-15 | SW1A 2AA        | SW1A                 | Detached             | Old            | Freehold        | GREATER LONDON | WESTMINSTER     | LONDON           |
      | 2         | 350000        | 2024-01-20 | SW1A 1AA        | SW1A                 | Detached             | Old            | Freehold        | GREATER LONDON | WESTMINSTER     | LONDON           |
      | 3         | 300000        | 2024-02-10 | SW1A 3BB        | SW1A                 | Detached             | Old            | Freehold        | GREATER LONDON | WESTMINSTER     | LONDON           |
    When I build the price paid fact table with location dimension
    Then the fact table should have columns year_month, location_id, property_type, old_new, min_price, median_price, max_price, transaction_count
    And the fact table should contain 2 rows

  Scenario: Fact table calculates min, median, max correctly
    Given the following silver layer data exists
      | id:string | price:integer | date:date  | postcode:string | postcode_area:string | property_type:string | old_new:string | duration:string | county:string  | district:string | town_city:string |
      | 1         | 100000        | 2024-01-15 | SW1A 2AA        | SW1A                 | Detached             | Old            | Freehold        | GREATER LONDON | WESTMINSTER     | LONDON           |
      | 2         | 200000        | 2024-01-20 | SW1A 1AA        | SW1A                 | Detached             | Old            | Freehold        | GREATER LONDON | WESTMINSTER     | LONDON           |
      | 3         | 300000        | 2024-01-25 | SW1A 3BB        | SW1A                 | Detached             | Old            | Freehold        | GREATER LONDON | WESTMINSTER     | LONDON           |
    When I build the price paid fact table with location dimension
    Then the aggregated row should have min_price 100000, median_price 200000, max_price 300000, transaction_count 3

  Scenario: Fact table has location_id foreign key from dimension join
    Given the following silver layer data exists
      | id:string | price:integer | date:date  | postcode:string | postcode_area:string | property_type:string | old_new:string | duration:string | county:string      | district:string | town_city:string |
      | 1         | 250000        | 2024-01-15 | SW1A 2AA        | SW1A                 | Detached             | Old            | Freehold        | GREATER LONDON     | WESTMINSTER     | LONDON           |
      | 2         | 300000        | 2024-01-20 | SW1A 1AA        | SW1A                 | Flat                 | New            | Leasehold       | GREATER LONDON     | WESTMINSTER     | LONDON           |
      | 3         | 175000        | 2024-01-10 | M1 1AE          | M1                   | Terraced             | Old            | Freehold        | GREATER MANCHESTER | MANCHESTER      | MANCHESTER       |
    When I build the price paid fact table with location dimension
    Then the fact table should have a column "location_id"
    And the fact table should not have columns county, district, town_city, postcode, postcode_area
