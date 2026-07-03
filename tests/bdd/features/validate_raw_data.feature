@unit
Feature: Validate price paid data

  Background:
    Given the following valid price paid data row exists
      | id:string                              | price:integer | date:date  | postcode:string | property_type:string | old_new:string | duration:string | paon:string | saon:string | street:string  | locality:string | town_city:string | district:string     | county:string  | ppd_category:string | record_type:string |
      | {4B6CB701-6A61-4B9C-8D1A-000000000001} |        500000 | 2024-03-15 | SW1A 2AA        | D                    | N              | F               | 10          |             | DOWNING STREET |                 | LONDON           | CITY OF WESTMINSTER | GREATER LONDON | A                   | A                  |

  Scenario: Valid data passes
    When I validate the price paid data
    Then the validation should pass without errors

  Scenario: Null id fails
    Given the id is null
    When I validate the price paid data
    Then the validation should fail with appropriate error messages

  Scenario: Null price fails
    Given the price is null
    When I validate the price paid data
    Then the validation should fail with appropriate error messages

  Scenario: Price of zero fails
    Given the price is 0
    When I validate the price paid data
    Then the validation should fail with appropriate error messages

  Scenario: Negative price fails
    Given the price is -1
    When I validate the price paid data
    Then the validation should fail with appropriate error messages

  Scenario: Null date fails
    Given the date is null
    When I validate the price paid data
    Then the validation should fail with appropriate error messages

  Scenario Outline: Invalid property type fails
    Given the property_type is "<value>"
    When I validate the price paid data
    Then the validation should fail with appropriate error messages

    Examples:
      | value |
      | X     |
      | d     |
      | 1     |

  Scenario Outline: Invalid old_new fails
    Given the old_new is "<value>"
    When I validate the price paid data
    Then the validation should fail with appropriate error messages

    Examples:
      | value |
      | X     |
      | y     |

  Scenario: Null duration fails
    Given the duration is null
    When I validate the price paid data
    Then the validation should fail with appropriate error messages

  Scenario Outline: Invalid ppd_category fails
    Given the ppd_category is "<value>"
    When I validate the price paid data
    Then the validation should fail with appropriate error messages

    Examples:
      | value |
      | C     |
      | a     |

  Scenario Outline: Invalid record_type fails
    Given the record_type is "<value>"
    When I validate the price paid data
    Then the validation should fail with appropriate error messages

    Examples:
      | value |
      | X     |
      | a     |

  Scenario: Five representative valid rows covering all categorical values
    Given the following valid price paid data row exists
      | id:string                              | price:integer | date:date  | postcode:string | property_type:string | old_new:string | duration:string | paon:string      | saon:string | street:string   | locality:string | town_city:string | district:string     | county:string      | ppd_category:string | record_type:string |
      | {B8AD0B85-A1B2-4C3D-8E4F-000000000001} |        525000 | 2024-03-15 | SW1A 2AA        | D                    | N              | F               | 10               |             | DOWNING STREET  |                 | LONDON           | CITY OF WESTMINSTER | GREATER LONDON     | A                   | A                  |
      | {B8AD0B85-A1B2-4C3D-8E4F-000000000002} |        285000 | 2024-04-22 | M1 1AE          | S                    | Y              | L               | 42               |             | PICCADILLY      | NORTHERN QUARTER| MANCHESTER       | MANCHESTER          | GREATER MANCHESTER | A                   | C                  |
      | {B8AD0B85-A1B2-4C3D-8E4F-000000000003} |        175000 | 2024-05-10 | EC1A 1BB        | T                    | N              | F               | 7                |             | ALDGATE         |                 | LONDON           | CITY OF LONDON      | GREATER LONDON     | B                   | D                  |
      | {B8AD0B85-A1B2-4C3D-8E4F-000000000004} |        425000 | 2024-06-01 | LS1 1BA         | F                    | Y              | L               | BRIDGEWATER PLACE| FLAT 5      | WATER LANE      | CITY CENTRE     | LEEDS            | LEEDS               | WEST YORKSHIRE     | A                   | A                  |
      | {B8AD0B85-A1B2-4C3D-8E4F-000000000005} |        320000 | 2024-07-14 |                 | O                    | N              | F               | 1                |             | HIGH STREET     |                 | BIRMINGHAM       | BIRMINGHAM          | WEST MIDLANDS      | B                   | A                  |
    When I validate the price paid data
    Then the validation should pass without errors
