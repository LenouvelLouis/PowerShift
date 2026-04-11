Feature: US-02 — Equal distribution across all houses
  As a grid operator,
  I want the 100 MWh to be split equally across 10 houses,
  so that the supply contract is respected.

  Background:
    Given a generator with 100 MW capacity
    And 10 houses each demanding 10 MW
    And a transformer connecting the grid

  Scenario: Total generation matches total consumption
    When I run a 1-hour simulation
    Then total supply is 100.0 MWh
    And total demand is 100.0 MWh
    And the energy balance is 0.0 MWh

  Scenario: No house receives more or less than the others
    When I run a 1-hour simulation
    Then every house receives the same amount of energy

  Scenario: Transformer distributes symmetrically
    When I run a 1-hour simulation
    Then the simulation status is "optimized"
    And no house deviates more than 1% from the mean consumption
