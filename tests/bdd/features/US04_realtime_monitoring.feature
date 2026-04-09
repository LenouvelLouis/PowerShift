Feature: US-04 — Real-time monitoring
  As an operator,
  I want to visualize each house's consumption in real time,
  so that I can confirm the system is working correctly.

  Background:
    Given a generator with 100 MW capacity
    And 10 houses each demanding 10 MW
    And a transformer connecting the grid

  Scenario: Simulation result contains data for all 10 houses
    When I run a 1-hour simulation
    Then the result includes load data for 10 houses

  Scenario: Time-series data is available for the full hour
    When I run a 1-hour simulation
    Then each house has a load time-series of length 1

  Scenario: Generator dispatch data is available
    When I run a 1-hour simulation
    Then the result includes generator dispatch data
    And the generator dispatch covers the full simulation period
