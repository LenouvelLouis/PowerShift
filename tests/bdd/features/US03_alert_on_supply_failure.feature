Feature: US-03 — Alert on supply failure
  As an operator,
  I want to be alerted if a house stops receiving energy,
  so that I can intervene before the 1-hour window ends.

  Background:
    Given a generator with 100 MW capacity
    And 10 houses each demanding 10 MW
    And a transformer connecting the grid

  Scenario: Simulation detects insufficient supply
    Given the generator capacity is reduced to 50 MW
    When I run a 1-hour simulation
    Then the simulation status is not "optimal"

  Scenario: Other houses are not impacted when supply is sufficient
    When I run a 1-hour simulation
    Then the simulation status is "optimal"
    And each house should receive between 9.9 and 10.1 MWh

  Scenario: Failure information is included in the result
    Given the generator capacity is reduced to 50 MW
    When I run a 1-hour simulation
    Then the simulation result contains error details
