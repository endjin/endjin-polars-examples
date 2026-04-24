@unit
Feature: Build a date dimension

  Scenario: Monthly date dimension is built correctly for a given date range
    Given the date dimension start date is '2026-01-15' and the end date is '2026-03-20'
    When I build the date dimension
    Then the date dimension should include the following months
      | year_month:string | year:int | quarter:int | month:int | month_name:string |
      | 2026-01            |     2026 |           1 |         1 | January           |
      | 2026-02            |     2026 |           1 |         2 | February          |
      | 2026-03            |     2026 |           1 |         3 | March             |

  Scenario: Date dimension includes quarter correctly across year boundaries
    Given the date dimension start date is '2025-10-01' and the end date is '2026-01-31'
    When I build the date dimension
    Then the date dimension should include the following months
      | year_month:string | year:int | quarter:int | month:int | month_name:string |
      | 2025-10            |     2025 |           4 |        10 | October           |
      | 2025-11            |     2025 |           4 |        11 | November          |
      | 2025-12            |     2025 |           4 |        12 | December          |
      | 2026-01            |     2026 |           1 |         1 | January           |
