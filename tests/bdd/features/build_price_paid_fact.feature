@unit
Feature: Build a price paid fact table

  Scenario: Fact table contains correct columns with foreign keys
    Given the following silver layer data exists
      | id:string | price:integer | date:date  | postcode:string | postcode_area:string | property_type:string | old_new:string | duration:string | county:string  | district:string | town_city:string |
      | 1         | 250000        | 2024-01-15 | SW1A 2AA        | SW1A                 | Detached             | Old            | Freehold        | GREATER LONDON | WESTMINSTER     | LONDON           |
      | 2         | 300000        | 2024-02-20 | M1 1AE          | M1                   | Flat                 | New            | Leasehold       | GREATER MANCHESTER | MANCHESTER  | MANCHESTER       |
    When I build the price paid fact table
    Then the fact table should contain 2 rows
    And the fact table should have columns price, date_of_transfer, postcode, postcode_area, town_city, property_type, old_new
    And the fact table should not have columns id, duration, county, district

  Scenario: Fact table renames date column to date_of_transfer
    Given the following silver layer data exists
      | id:string | price:integer | date:date  | postcode:string | postcode_area:string | property_type:string | old_new:string | duration:string | county:string  | district:string | town_city:string |
      | 1         | 250000        | 2024-03-10 | BS1 5AH         | BS1                  | Terraced             | Old            | Freehold        | AVON           | BRISTOL         | BRISTOL          |
    When I build the price paid fact table
    Then the date_of_transfer column should contain "2024-03-10"
