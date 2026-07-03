@unit
Feature: Build a daily date dimension

  Scenario: Daily date dimension is built correctly for a short date range
    Given the daily date dimension start date is '2026-01-01' and the end date is '2026-01-03'
    When I build the daily date dimension
    Then the daily date dimension should contain 3 rows
    And the daily date dimension should include the following data
      | date:date  | year_month:string | year:int | quarter:int | month:int | month_name:string | day_of_month:int | day_name:string | week:int | weekday:int | is_weekend:bool | day_of_year:int |
      | 2026-01-01 | 2026-01           |     2026 |           1 |         1 | January           |                1 | Thursday        |        1 |           4 | false           |               1 |
      | 2026-01-02 | 2026-01           |     2026 |           1 |         1 | January           |                2 | Friday          |        1 |           5 | false           |               2 |
      | 2026-01-03 | 2026-01           |     2026 |           1 |         1 | January           |                3 | Saturday        |        1 |           6 | true            |               3 |

  Scenario: Daily date dimension spans weekends correctly
    Given the daily date dimension start date is '2026-03-06' and the end date is '2026-03-09'
    When I build the daily date dimension
    Then the daily date dimension should include the following data
      | date:date  | day_name:string | weekday:int | is_weekend:bool |
      | 2026-03-06 | Friday          |           5 | false           |
      | 2026-03-07 | Saturday        |           6 | true            |
      | 2026-03-08 | Sunday          |           7 | true            |
      | 2026-03-09 | Monday          |           1 | false           |

  Scenario: Daily date dimension crosses quarter boundaries
    Given the daily date dimension start date is '2026-03-31' and the end date is '2026-04-02'
    When I build the daily date dimension
    Then the daily date dimension should include the following data
      | date:date  | year_month:string | quarter:int | month:int | month_name:string |
      | 2026-03-31 | 2026-03           |           1 |         3 | March             |
      | 2026-04-01 | 2026-04           |           2 |         4 | April             |
      | 2026-04-02 | 2026-04           |           2 |         4 | April             |

  Scenario: Daily date dimension crosses year boundaries
    Given the daily date dimension start date is '2025-12-30' and the end date is '2026-01-02'
    When I build the daily date dimension
    Then the daily date dimension should include the following data
      | date:date  | year:int | day_of_year:int | week:int |
      | 2025-12-30 |     2025 |             364 |        1 |
      | 2025-12-31 |     2025 |             365 |        1 |
      | 2026-01-01 |     2026 |               1 |        1 |
      | 2026-01-02 |     2026 |               2 |        1 |

  Scenario: Single day date dimension
    Given the daily date dimension start date is '2026-06-15' and the end date is '2026-06-15'
    When I build the daily date dimension
    Then the daily date dimension should contain 1 rows
    And the daily date dimension should include the following data
      | date:date  | year_month:string | year:int | quarter:int | month:int | month_name:string | day_of_month:int | day_name:string |
      | 2026-06-15 | 2026-06           |     2026 |           2 |         6 | June              |               15 | Monday          |
