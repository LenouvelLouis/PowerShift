Feature: US-01 — Constant energy delivery
  As a house connected to the grid,
  I want to receive exactly 10 MWh over 1 hour,
  so that my consumption is guaranteed without interruption.

  Background:
    Given a generator with 100 MW capacity
    And 10 houses each demanding 10 MW
    And a transformer connecting the grid

  Scenario: Each house receives 10 MWh within tolerance
    When I run a 1-hour simulation
    Then each house should receive between 9.9 and 10.1 MWh

  Scenario: Delivery is continuous for the full hour
    When I run a 1-hour simulation
    Then no house has a zero-power gap in its load series

  Scenario: Simulation completes without interruption
    When I run a 1-hour simulation
    Then the simulation status is "optimal"
    And the total demand is 100.0 MWh
