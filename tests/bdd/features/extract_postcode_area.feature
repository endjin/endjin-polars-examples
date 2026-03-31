@unit
Feature: Extract postcode area

  Scenario: Extract postcode area from full postcode
    Given a dataset with the following rows
      | postcode:string |
      | AB12 3CD        |
      | XY99 9ZZ        |
    When I extract the postcode area from the full postcode
    Then the resulting dataset should include the following rows
      | postcode_area:string |
      | AB                   |
      | XY                   |

  Scenario: Handle postcodes without spaces correctly
    Given a dataset with the following rows
      | postcode:string |
      | AB123CD         |
      | XY999ZZ         |
    When I extract the postcode area from the full postcode
    Then the resulting dataset should include the following rows
      | postcode_area:string |
      | AB                   |
      | XY                   |

  Scenario: Handle empty or null postcodes correctly
    Given a dataset with the following rows
      | postcode:string |
      |                  |
      | null             |
    When I extract the postcode area from the full postcode
    Then the resulting dataset should include the following rows
      | postcode_area:string |
      |                      |
      | null                 |